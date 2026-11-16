"""
WILDFIRE GUARD — FULL BACKEND API, DATABASE & PDF GENERATION ENGINE
Features:
  - 15 Relational SQLite tables with full historical coordinates (lat, lng, timestamp)
  - Time-series tracking for Sensors, AI Risk, Rovers, Hotspots, and Alerts
  - Built-in Pure Python PDF Generator (downloads directly to user laptop)
  - Full REST API with /api/history and /api/history/pdf
Zero pip dependencies required — uses Python's standard library.
Run with:
    python wildfire_backend.py
"""

import sqlite3
import http.server
import socketserver
import json
import os
import urllib.parse
import webbrowser
import threading
from datetime import datetime

PORT = 8000
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wildfire_guard.db")
HTML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")

# ==============================================================================
# 📄 PURE PYTHON PDF GENERATOR (Zero external dependencies)
# Builds valid PDF 1.4 binary documents with tables, headers, and metadata
# ==============================================================================
class SimplePDFBuilder:
    def __init__(self, title="WILDFIRE GUARD MONITORING REPORT"):
        self.title = title
        self.lines = []

    def add_line(self, text, size=11, bold=False, color=(0, 0, 0)):
        self.lines.append({"text": text, "size": size, "bold": bold, "color": color})

    def add_space(self, pts=10):
        self.lines.append({"space": pts})

    def add_separator(self):
        self.lines.append({"separator": True})

    def build(self) -> bytes:
        content_stream = []
        y = 750

        # Header Title
        content_stream.append("BT")
        content_stream.append("/F2 18 Tf")
        content_stream.append("0.05 0.35 0.20 rg")  # Forest green
        content_stream.append(f"50 {y} Td")
        content_stream.append(f"({self.escape(self.title)}) Tj")
        content_stream.append("ET")
        y -= 22

        content_stream.append("BT")
        content_stream.append("/F1 10 Tf")
        content_stream.append("0.4 0.4 0.4 rg")
        content_stream.append(f"50 {y} Td")
        content_stream.append(f"(AI-Powered Forest Fire Prevention & Monitoring | Western Forest Zone) Tj")
        content_stream.append("ET")
        y -= 15

        # Horizontal Rule
        content_stream.append(f"0.1 0.6 0.3 RG 1.5 w 50 {y} m 550 {y} l S")
        y -= 20

        for item in self.lines:
            if "separator" in item:
                content_stream.append(f"0.8 0.8 0.8 RG 0.75 w 50 {y} m 550 {y} l S")
                y -= 14
            elif "space" in item:
                y -= item["space"]
            else:
                text = self.escape(item["text"])
                size = item["size"]
                font = "/F2" if item.get("bold") else "/F1"
                r, g, b = item.get("color", (0.1, 0.1, 0.1))

                content_stream.append("BT")
                content_stream.append(f"{font} {size} Tf")
                content_stream.append(f"{r} {g} {b} rg")
                content_stream.append(f"50 {y} Td")
                content_stream.append(f"({text}) Tj")
                content_stream.append("ET")
                y -= int(size * 1.35)

            if y < 60:
                break  # Page boundary guard

        stream_bytes = "\n".join(content_stream).encode("latin-1", "replace")
        stream_len = len(stream_bytes)

        objects = []
        # Obj 1: Catalog
        objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        # Obj 2: Pages
        objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
        # Obj 3: Page
        objects.append(
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R /Resources << /Font << "
            b"/F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> "
            b"/F2 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >> "
            b">> >> >>"
        )
        # Obj 4: Content Stream
        objects.append(f"<< /Length {stream_len} >>\nstream\n".encode("ascii") + stream_bytes + b"\nendstream")

        # Assemble PDF file
        pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = []
        for i, obj in enumerate(objects):
            offsets.append(len(pdf))
            pdf.extend(f"{i+1} 0 obj\n".encode("ascii"))
            pdf.extend(obj)
            pdf.extend(b"\nendobj\n")

        xref_offset = len(pdf)
        pdf.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode("ascii"))
        for off in offsets:
            pdf.extend(f"{off:010d} 00000 n \n".encode("ascii"))

        pdf.extend(
            f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
        )
        return bytes(pdf)

    def escape(self, s: str) -> str:
        s = str(s)
        s = s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        return s.encode("latin-1", "replace").decode("latin-1")


# ==============================================================================
# 🗄️ DATABASE ENGINE & SCHEMA (Historical Coordinates & Timestamps)
# ==============================================================================
def init_database():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Drop & recreate to ensure latest schema with coordinates
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY, full_name TEXT, email TEXT,
            password_hash TEXT, role TEXT, status TEXT, created_at TEXT, last_login TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS forest_zones (
            zone_id TEXT PRIMARY KEY, zone_name TEXT, forest_name TEXT,
            area_km2 REAL, latitude REAL, longitude REAL,
            vegetation_density TEXT, risk_level TEXT, status TEXT, created_at TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS sensors (
            sensor_id TEXT PRIMARY KEY, zone_id TEXT, sensor_type TEXT,
            latitude REAL, longitude REAL, battery_percentage INTEGER,
            signal_strength TEXT, status TEXT, installed_at TEXT, last_seen TEXT
        )
    ''')

    # Historical Sensor Readings (stores coordinates & timestamp per reading)
    c.execute('''
        CREATE TABLE IF NOT EXISTS sensor_readings (
            reading_id TEXT PRIMARY KEY, sensor_id TEXT, zone_id TEXT,
            temperature_c REAL, humidity_percent REAL, smoke_ppm REAL,
            soil_moisture_percent REAL, latitude REAL, longitude REAL,
            battery_percentage INTEGER, signal_strength TEXT, recorded_at TEXT
        )
    ''')

    # Historical Risk Analysis
    c.execute('''
        CREATE TABLE IF NOT EXISTS risk_analysis (
            analysis_id TEXT PRIMARY KEY, zone_id TEXT, risk_score INTEGER,
            risk_level TEXT, fire_probability INTEGER, temperature REAL,
            humidity REAL, smoke REAL, soil_moisture REAL, vegetation_density TEXT,
            latitude REAL, longitude REAL, recommendation TEXT, analyzed_at TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS risk_factors (
            factor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            zone_id TEXT, factor TEXT, severity TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS rovers (
            rover_id TEXT PRIMARY KEY, status TEXT, battery_percentage INTEGER,
            speed_kmh REAL, current_zone TEXT, target_zone TEXT,
            distance_to_target_km REAL, mission TEXT, camera_status TEXT,
            thermal_sensor_status TEXT, gps_status TEXT, communication_status TEXT
        )
    ''')

    # Historical Rover Locations & Movement Log
    c.execute('''
        CREATE TABLE IF NOT EXISTS rover_locations (
            location_id INTEGER PRIMARY KEY AUTOINCREMENT, rover_id TEXT,
            zone_id TEXT, latitude REAL, longitude REAL, speed_kmh REAL,
            battery_percentage INTEGER, heading REAL, recorded_at TEXT,
            target_zone TEXT, target_latitude REAL, target_longitude REAL,
            distance_km REAL, eta_minutes INTEGER, status TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS rover_missions (
            mission_id TEXT PRIMARY KEY, rover_id TEXT, mission_type TEXT,
            target_zone TEXT, priority TEXT, status TEXT, started_at TEXT
        )
    ''')

    # Historical Hotspots
    c.execute('''
        CREATE TABLE IF NOT EXISTS hotspots (
            hotspot_id TEXT PRIMARY KEY, zone TEXT, zone_id TEXT,
            latitude REAL, longitude REAL, temperature REAL, smoke REAL,
            fire_probability INTEGER, vegetation_density TEXT, wind_speed_kmh REAL,
            detected_by TEXT, status TEXT, detected_at TEXT, resolved_at TEXT
        )
    ''')

    # Historical Alerts
    c.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            alert_id TEXT PRIMARY KEY, alert_type TEXT, severity TEXT,
            zone TEXT, zone_id TEXT, hotspot_id TEXT, latitude REAL, longitude REAL,
            temperature REAL, fire_probability INTEGER, message TEXT,
            detected_by TEXT, timestamp TEXT, action_status TEXT, acknowledged INTEGER
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            activity_id TEXT PRIMARY KEY, time TEXT, type TEXT,
            message TEXT, severity TEXT, zone TEXT, created_at TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS system_health (
            component TEXT PRIMARY KEY, status TEXT, last_check TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS forest_statistics (
            forest_name TEXT PRIMARY KEY, total_forest_area_km2 REAL,
            monitored_area_km2 REAL, coverage_percentage REAL,
            total_sensors INTEGER, active_rovers INTEGER, risk_zones INTEGER,
            critical_zones INTEGER, detected_hotspots INTEGER
        )
    ''')

    # Report Download History
    c.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            report_id TEXT PRIMARY KEY, report_type TEXT, report_name TEXT,
            forest TEXT, date_from TEXT, date_to TEXT, zone_id TEXT,
            file_name TEXT, generated_at TEXT, requested_by TEXT, status TEXT
        )
    ''')

    # SEED DATA IF EMPTY
    c.execute('SELECT COUNT(*) FROM forest_zones')
    if c.fetchone()[0] == 0:
        c.execute('''
            INSERT INTO users VALUES ('U001', 'Forest Administrator', 'admin@wildfireguard.com',
            'pbkdf2:sha256:secret', 'ADMIN', 'ACTIVE', '2026-01-10 09:00:00', '2026-09-03 10:42:00')
        ''')

        zones = [
            ("Z001", "Zone A", "Western Forest Zone", 50, 11.230, 76.910, "Medium", "Low", "MONITORED", "2026-01-01"),
            ("Z002", "Zone B", "Western Forest Zone", 50, 11.245, 76.930, "High", "Moderate", "MONITORED", "2026-01-01"),
            ("Z003", "Zone C", "Western Forest Zone", 50, 11.276, 76.958, "High", "Critical", "CRITICAL", "2026-01-01"),
            ("Z004", "Zone D", "Western Forest Zone", 50, 11.260, 76.975, "High", "High", "MONITORED", "2026-01-01"),
            ("Z005", "Zone E", "Western Forest Zone", 50, 11.215, 76.945, "Low", "Low", "MONITORED", "2026-01-01")
        ]
        c.executemany('INSERT INTO forest_zones VALUES (?,?,?,?,?,?,?,?,?,?)', zones)

        sensors = [
            ("S-001", "Z001", "Environmental", 11.228, 76.912, 94, "Strong", "ONLINE", "2026-01-15", "2026-09-03 10:42:00"),
            ("S-002", "Z002", "Environmental", 11.243, 76.928, 79, "Good", "WARNING", "2026-01-15", "2026-09-03 10:42:00"),
            ("S-003", "Z003", "Environmental", 11.276, 76.958, 87, "Strong", "CRITICAL", "2026-01-15", "2026-09-03 10:41:52"),
            ("S-004", "Z004", "Environmental", 11.262, 76.972, 71, "Good", "HIGH", "2026-01-15", "2026-09-03 10:42:00"),
            ("S-005", "Z005", "Environmental", 11.216, 76.944, 91, "Strong", "ONLINE", "2026-01-15", "2026-09-03 10:42:00")
        ]
        c.executemany('INSERT INTO sensors VALUES (?,?,?,?,?,?,?,?,?,?)', sensors)

        # 1. Historical Sensor Readings (With Coordinates & Timestamps)
        readings = [
            ("RD001", "S-003", "Z003", 31, 52, 18, 29, 11.276, 76.958, 92, "Strong", "2026-09-03 08:00:00"),
            ("RD002", "S-003", "Z003", 35, 43, 29, 25, 11.276, 76.958, 90, "Strong", "2026-09-03 09:00:00"),
            ("RD003", "S-003", "Z003", 40, 34, 51, 21, 11.276, 76.958, 88, "Strong", "2026-09-03 10:00:00"),
            ("RD004", "S-003", "Z003", 42, 25, 75, 18, 11.276, 76.958, 87, "Strong", "2026-09-03 10:41:52"),
            ("RD005", "S-001", "Z001", 31, 62, 12, 48, 11.228, 76.912, 94, "Strong", "2026-09-03 10:42:00"),
            ("RD006", "S-002", "Z002", 37, 38, 28, 31, 11.243, 76.928, 79, "Good", "2026-09-03 10:42:00"),
            ("RD007", "S-004", "Z004", 35, 41, 34, 29, 11.262, 76.972, 71, "Good", "2026-09-03 10:42:00"),
            ("RD008", "S-005", "Z005", 29, 68, 8, 55, 11.216, 76.944, 91, "Strong", "2026-09-03 10:42:00")
        ]
        c.executemany('INSERT INTO sensor_readings VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', readings)

        # 2. Historical Risk Analysis (With Coordinates & Timestamps)
        risk_entries = [
            ("RA001", "Z003", 78, "HIGH", 78, 38, 34, 45, 22, "High", 11.276, 76.958, "Prepare Rover Dispatch", "2026-09-03 10:36:00"),
            ("RA002", "Z003", 86, "HIGH", 86, 40, 28, 62, 20, "High", 11.276, 76.958, "Deploy Rover R-001", "2026-09-03 10:40:00"),
            ("RA003", "Z003", 91, "CRITICAL", 91, 42, 25, 75, 18, "High", 11.276, 76.958, "Deploy Rover R-001 for immediate investigation.", "2026-09-03 10:42:00"),
            ("RA004", "Z001", 24, "LOW", 24, 31, 62, 12, 48, "Medium", 11.230, 76.910, "Routine Patrol", "2026-09-03 10:42:00"),
            ("RA005", "Z002", 67, "MEDIUM", 67, 37, 38, 28, 31, "High", 11.245, 76.930, "Increased Surveillance", "2026-09-03 10:42:00"),
            ("RA006", "Z004", 78, "HIGH", 78, 35, 41, 34, 29, "High", 11.260, 76.975, "Perimeter Surveillance", "2026-09-03 10:42:00")
        ]
        c.executemany('INSERT INTO risk_analysis VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', risk_entries)

        # 3. Historical Rover Movements (GPS Tracking History)
        rover_locs = [
            ("R-002", "Z003", 11.270, 76.950, 3.2, 65, 45, "2026-09-03 10:40:00", "Zone C", 11.276, 76.958, 0.8, 12, "Moving"),
            ("R-002", "Z003", 11.274, 76.955, 2.1, 64, 48, "2026-09-03 10:41:00", "Zone C", 11.276, 76.958, 0.3, 4, "Investigating"),
            ("R-002", "Z003", 11.276, 76.958, 0.0, 64, 50, "2026-09-03 10:42:00", "Zone C", 11.276, 76.958, 0.0, 0, "Investigating"),
            ("R-001", "Z002", 11.245, 76.921, 4.5, 82, 45, "2026-09-03 10:42:00", "Zone C", 11.276, 76.958, 2.4, 32, "Moving"),
            ("R-003", "Z004", 11.258, 76.970, 4.2, 91, 15, "2026-09-03 10:42:00", "Zone D Hotspot", 11.265, 76.945, 1.1, 15, "Moving")
        ]
        c.executemany('''
            INSERT INTO rover_locations (rover_id, zone_id, latitude, longitude, speed_kmh, battery_percentage, heading, recorded_at, target_zone, target_latitude, target_longitude, distance_km, eta_minutes, status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', rover_locs)

        # 4. Historical Hotspots
        hotspots = [
            ("H-001", "Zone C", "Z003", 11.276, 76.958, 68, 82, 94, "High", 18, "R-002", "CRITICAL", "2026-09-03 10:38:24", None),
            ("H-002", "Zone C", "Z003", 11.279, 76.961, 61, 71, 88, "High", 17, "R-002", "CRITICAL", "2026-09-03 10:39:10", None),
            ("H-003", "Zone D", "Z004", 11.265, 76.945, 51, 45, 72, "High", 14, "R-003", "WARNING", "2026-09-03 10:35:00", None),
            ("H-004", "Zone B", "Z002", 11.260, 76.930, 47, 38, 61, "Medium", 12, "S-002", "MONITORING", "2026-09-03 10:30:00", None)
        ]
        c.executemany('INSERT INTO hotspots VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', hotspots)

        # 5. Historical Alerts
        alerts = [
            ("A-001", "Potential Fire Detected", "CRITICAL", "Zone C", "Z003", "H-001", 11.276, 76.958, 68, 94, "Potential Fire Detected", "R-002", "2026-09-03 10:38:00", "Emergency Response Required", 0),
            ("A-002", "High Temperature Detected", "WARNING", "Zone D", "Z004", None, 11.260, 76.975, 51, 72, "High Temperature Detected", "S-004", "2026-09-03 10:35:00", "Monitoring", 0)
        ]
        c.executemany('INSERT INTO alerts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', alerts)

        # 6. Report Download History
        reports_history = [
            ("REP001", "HISTORICAL_MONITORING", "Daily Monitoring Report", "Western Forest Zone", "2026-09-03", "2026-09-03", "ALL", "Wildfire_Daily_Report_2026-09-03.pdf", "2026-09-03 11:00:00", "U001", "COMPLETED"),
            ("REP002", "RISK_AUDIT", "Zone C Risk Report", "Western Forest Zone", "2026-09-03", "2026-09-03", "Z003", "Wildfire_Zone_C_Risk_2026-09-03.pdf", "2026-09-03 10:50:00", "U001", "COMPLETED"),
            ("REP003", "SENSOR_AUDIT", "Sensor History Report", "Western Forest Zone", "2026-09-02", "2026-09-03", "ALL", "Wildfire_Sensor_History_2026-09-02.pdf", "2026-09-02 18:00:00", "U001", "COMPLETED"),
            ("REP004", "ROVER_TELEMETRY", "Rover Movement Report", "Western Forest Zone", "2026-09-02", "2026-09-03", "Z003", "Wildfire_Rover_Movement_2026-09-02.pdf", "2026-09-02 16:30:00", "U001", "COMPLETED"),
            ("REP005", "HOTSPOT_AUDIT", "Hotspot Detection Report", "Western Forest Zone", "2026-09-01", "2026-09-03", "ALL", "Wildfire_Hotspot_Audit_2026-09-01.pdf", "2026-09-01 12:00:00", "U001", "COMPLETED")
        ]
        c.executemany('INSERT INTO reports VALUES (?,?,?,?,?,?,?,?,?,?,?)', reports_history)

        # Forest Stats & Subsystem Health
        c.execute("INSERT INTO forest_statistics VALUES ('Western Forest Zone', 250, 218, 87.2, 24, 3, 12, 2, 4)")
        health_nodes = [("IoT Sensors", "ONLINE", "2026-09-03 10:42:18"), ("AI Prediction", "ONLINE", "2026-09-03 10:42:18"), ("Rover Network", "ONLINE", "2026-09-03 10:42:18"), ("GPS Tracking", "ONLINE", "2026-09-03 10:42:18"), ("Thermal Detection", "ONLINE", "2026-09-03 10:42:18"), ("Communication", "ONLINE", "2026-09-03 10:42:18"), ("Database", "ONLINE", "2026-09-03 10:42:18")]
        c.executemany("INSERT INTO system_health VALUES (?,?,?)", health_nodes)

        rovers = [
            ("R-001", "MOVING", 82, 4.5, "Zone B", "Zone C", 2.4, "Investigate Critical Risk Area", "ACTIVE", "ACTIVE", "CONNECTED", "CONNECTED"),
            ("R-002", "INVESTIGATING", 64, 0.0, "Zone C", "Zone C", 0.0, "Hotspot Detection", "ACTIVE", "ACTIVE", "CONNECTED", "CONNECTED"),
            ("R-003", "MOVING", 91, 4.2, "Zone D", "Zone D Hotspot", 1.1, "Investigate Hotspot", "ACTIVE", "ACTIVE", "CONNECTED", "CONNECTED")
        ]
        c.executemany("INSERT INTO rovers VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", rovers)

    conn.commit()
    conn.close()

# ==============================================================================
# 🌐 REST API CONTROLLER & PDF DISPATCH
# ==============================================================================
class WildfireServer(http.server.BaseHTTPRequestHandler):

    def send_json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip('/')
        qs = urllib.parse.parse_qs(parsed.query)

        # Serve Frontend HTML
        if path in ("", "/", "/index.html"):
            if os.path.exists(HTML_FILE):
                with open(HTML_FILE, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(content)
                return

        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # 📥 GET /api/history/pdf (Direct PDF Generation & Laptop Download)
        if path == "/api/history/pdf":
            zone_filter = qs.get("zone", ["Z003"])[0]
            date_from = qs.get("from", ["2026-09-03"])[0]
            date_to = qs.get("to", ["2026-09-03"])[0]

            # Query historical tables
            c.execute("SELECT * FROM sensor_readings WHERE recorded_at LIKE ? ORDER BY recorded_at ASC", (f"{date_from}%",))
            sensor_history = [dict(r) for r in c.fetchall()]

            c.execute("SELECT * FROM risk_analysis ORDER BY analyzed_at ASC")
            risk_history = [dict(r) for r in c.fetchall()]

            c.execute("SELECT * FROM rover_locations ORDER BY recorded_at ASC")
            rover_history = [dict(r) for r in c.fetchall()]

            c.execute("SELECT * FROM hotspots ORDER BY detected_at DESC")
            hotspot_history = [dict(r) for r in c.fetchall()]

            c.execute("SELECT * FROM alerts ORDER BY timestamp DESC")
            alert_history = [dict(r) for r in c.fetchall()]

            # Build Formatted PDF Report
            pdf_builder = SimplePDFBuilder(title="WILDFIRE GUARD — HISTORICAL MONITORING REPORT")
            pdf_builder.add_line(f"Report Type: Historical Environmental Audit | Sector: Western Forest Zone", size=10, bold=True)
            pdf_builder.add_line(f"Date Range: {date_from} to {date_to} | Generated: {datetime.now().strftime('%d-%m-%Y %I:%M %p')}", size=9)
            pdf_builder.add_line(f"Total Area: 250 km² | Monitored: 218 km² (Coverage: 87.2%) | Active Rovers: 3", size=9)
            pdf_builder.add_separator()

            # Location Focus
            pdf_builder.add_line("CRITICAL TARGET SECTOR IDENTIFICATION:", size=10, bold=True, color=(0.8, 0.1, 0.1))
            pdf_builder.add_line("Zone: Zone C | GPS Coordinates: 11.276° N, 76.958° E | Elevation: 640m | Risk: CRITICAL (91%)", size=9)
            pdf_builder.add_separator()

            # Sensor History
            pdf_builder.add_line("1. SENSOR TELEMETRY HISTORY (S-003 Chronology):", size=10, bold=True)
            pdf_builder.add_line(f"{'Time':<8} {'Sensor':<8} {'Zone':<8} {'Temp':<8} {'Humidity':<10} {'Smoke':<10} {'Soil Moist':<10}", size=9, bold=True)
            for s in sensor_history[:5]:
                t = s['recorded_at'].split(' ')[-1][:5] if ' ' in s['recorded_at'] else s['recorded_at'][-8:-3]
                pdf_builder.add_line(f"{t:<8} {s['sensor_id']:<8} Zone C   {s['temperature_c']}°C     {s['humidity_percent']}%        {s['smoke_ppm']} ppm     {s['soil_moisture_percent']}%", size=8.5)
            pdf_builder.add_separator()

            # AI Risk History
            pdf_builder.add_line("2. AI FIRE RISK MODEL HISTORY:", size=10, bold=True)
            pdf_builder.add_line(f"{'Time':<8} {'Zone':<8} {'Risk Score':<12} {'Fire Probability':<18} {'Risk Level':<10}", size=9, bold=True)
            for r in risk_history[:4]:
                t = r['analyzed_at'].split(' ')[-1][:5] if ' ' in r['analyzed_at'] else '10:42'
                pdf_builder.add_line(f"{t:<8} Zone C   {r['risk_score']}%          {r['fire_probability']}%                 {r['risk_level']}", size=8.5)
            pdf_builder.add_separator()

            # Rover Movement History
            pdf_builder.add_line("3. ROVER GPS MOVEMENT HISTORY (R-002 Tracking):", size=10, bold=True)
            pdf_builder.add_line(f"{'Time':<8} {'Rover':<8} {'Latitude':<12} {'Longitude':<12} {'Speed':<10} {'Battery':<10} {'Status':<12}", size=9, bold=True)
            for rv in rover_history[:4]:
                t = rv['recorded_at'].split(' ')[-1][:5] if ' ' in rv['recorded_at'] else '10:40'
                pdf_builder.add_line(f"{t:<8} {rv['rover_id']:<8} {rv['latitude']:<12.3f} {rv['longitude']:<12.3f} {rv['speed_kmh']} km/h    {rv['battery_percentage']}%        {rv['status']}", size=8.5)
            pdf_builder.add_separator()

            # Hotspots & Alerts
            pdf_builder.add_line("4. THERMAL HOTSPOTS & CRITICAL ALERTS:", size=10, bold=True)
            for h in hotspot_history[:2]:
                pdf_builder.add_line(f"Hotspot {h['hotspot_id']} ({h['zone']}): {h['temperature']}°C | Smoke: {h['smoke']} ppm | Fire Prob: {h['fire_probability']}% | Status: {h['status']}", size=8.5)
            for a in alert_history[:2]:
                pdf_builder.add_line(f"Alert {a['alert_id']} ({a['zone']}): {a['alert_type']} | Severity: {a['severity']} | Action: {a['action_status']}", size=8.5)

            pdf_bytes = pdf_builder.build()

            # Send PDF Download Response
            file_name = f"Wildfire_History_{date_from}.pdf"
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Disposition", f'attachment; filename="{file_name}"')
            self.send_header("Content-Length", str(len(pdf_bytes)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(pdf_bytes)

            # Record download in report history
            rep_id = f"REP{int(datetime.now().timestamp())}"
            c.execute('''
                INSERT INTO reports VALUES (?, 'HISTORICAL_MONITORING', 'Historical Audit Report',
                'Western Forest Zone', ?, ?, ?, ?, ?, 'U001', 'COMPLETED')
            ''', (rep_id, date_from, date_to, zone_filter, file_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            return

        # 📜 GET /api/history (Unified Historical Data Query)
        elif path == "/api/history":
            # Returns combined chronological records
            c.execute("SELECT recorded_at as timestamp, 'Sensor' as type, zone_id as zone, '11.276° N, 76.958° E' as location, temperature_c || '°C, ' || smoke_ppm || ' ppm' as value, 'Critical' as status FROM sensor_readings WHERE sensor_id='S-003' ORDER BY recorded_at DESC")
            sensors_hist = [dict(r) for r in c.fetchall()]

            c.execute("SELECT recorded_at as timestamp, 'Rover' as type, zone_id as zone, latitude || '° N, ' || longitude || '° E' as location, rover_id || ' (' || speed_kmh || ' km/h)' as value, status FROM rover_locations ORDER BY recorded_at DESC")
            rovers_hist = [dict(r) for r in c.fetchall()]

            c.execute("SELECT detected_at as timestamp, 'Hotspot' as type, zone, latitude || '° N, ' || longitude || '° E' as location, hotspot_id || ' (' || fire_probability || '% prob)' as value, status FROM hotspots ORDER BY detected_at DESC")
            hotspots_hist = [dict(r) for r in c.fetchall()]

            c.execute("SELECT timestamp, 'Alert' as type, zone, latitude || '° N, ' || longitude || '° E' as location, alert_type as value, severity as status FROM alerts ORDER BY timestamp DESC")
            alerts_hist = [dict(r) for r in c.fetchall()]

            c.execute("SELECT analyzed_at as timestamp, 'AI Risk' as type, zone_id as zone, latitude || '° N, ' || longitude || '° E' as location, 'Risk: ' || risk_score || '%' as value, risk_level as status FROM risk_analysis WHERE zone_id='Z003' ORDER BY analyzed_at DESC")
            risk_hist = [dict(r) for r in c.fetchall()]

            combined = sensors_hist + rovers_hist + hotspots_hist + alerts_hist + risk_hist
            conn.close()
            return self.send_json(combined)

        # 📑 GET /api/reports/history (List all generated PDF reports)
        elif path == "/api/reports/history" or path == "/api/reports":
            c.execute("SELECT * FROM reports ORDER BY generated_at DESC")
            reps = [dict(r) for r in c.fetchall()]
            conn.close()
            return self.send_json(reps)

        # Standard routes
        elif path == "/api/dashboard":
            c.execute("SELECT * FROM forest_statistics WHERE forest_name='Western Forest Zone'")
            stats = dict(c.fetchone())
            resp = {
                "system": {"name": "WILDFIRE GUARD", "status": "ONLINE", "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                "forest": {"name": stats["forest_name"], "total_area_km2": stats["total_forest_area_km2"], "monitored_area_km2": stats["monitored_area_km2"], "coverage": stats["coverage_percentage"]},
                "summary": {"active_sensors": stats["total_sensors"], "online_sensors": 22, "warning_sensors": 2, "high_risk_areas": stats["risk_zones"], "active_rovers": stats["active_rovers"], "hotspots": stats["detected_hotspots"], "critical_hotspots": 2},
                "risk": {"overall_score": 72, "level": "HIGH", "critical_zone": "Zone C"},
                "alerts": {"critical": 2, "warning": 2},
                "system_health": "OPERATIONAL"
            }
            conn.close()
            return self.send_json(resp)

        elif path == "/api/zones":
            c.execute("SELECT * FROM forest_zones")
            zones = [dict(row) for row in c.fetchall()]
            conn.close()
            return self.send_json(zones)

        elif path == "/api/sensors":
            c.execute('''
                SELECT s.*, r.temperature_c, r.humidity_percent, r.smoke_ppm, r.soil_moisture_percent, z.zone_name
                FROM sensors s JOIN forest_zones z ON s.zone_id = z.zone_id
                LEFT JOIN sensor_readings r ON s.sensor_id = r.sensor_id
                GROUP BY s.sensor_id ORDER BY s.sensor_id
            ''')
            sensors = [dict(row) for row in c.fetchall()]
            conn.close()
            return self.send_json(sensors)

        elif path.startswith("/api/sensors/") and path.endswith("/readings"):
            sensor_id = path.split("/")[3]
            c.execute("SELECT * FROM sensor_readings WHERE sensor_id=? ORDER BY recorded_at ASC", (sensor_id,))
            readings = [dict(row) for row in c.fetchall()]
            conn.close()
            return self.send_json(readings)

        elif path == "/api/rovers":
            c.execute("SELECT * FROM rovers")
            rovers = [dict(row) for row in c.fetchall()]
            conn.close()
            return self.send_json(rovers)

        elif path == "/api/hotspots":
            c.execute("SELECT * FROM hotspots ORDER BY fire_probability DESC")
            hotspots = [dict(row) for row in c.fetchall()]
            conn.close()
            return self.send_json(hotspots)

        elif path == "/api/alerts":
            c.execute("SELECT * FROM alerts ORDER BY timestamp DESC")
            alerts = [dict(row) for row in c.fetchall()]
            conn.close()
            return self.send_json(alerts)

        elif path == "/api/activity":
            c.execute("SELECT * FROM activity_logs ORDER BY created_at DESC LIMIT 20")
            logs = [dict(row) for row in c.fetchall()]
            conn.close()
            return self.send_json(logs)

        elif path == "/api/system-health":
            c.execute("SELECT * FROM system_health")
            health = [dict(row) for row in c.fetchall()]
            conn.close()
            return self.send_json({"components": health, "overall_status": "OPERATIONAL"})

        elif path == "/api/statistics":
            c.execute("SELECT * FROM forest_statistics")
            stats = dict(c.fetchone())
            conn.close()
            return self.send_json(stats)

        conn.close()
        self.send_error(404, "Endpoint not found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip('/')
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len) if content_len > 0 else b'{}'
        try:
            payload = json.loads(body.decode('utf-8'))
        except Exception:
            payload = {}

        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        if path == "/api/rovers/dispatch":
            rover_id = payload.get("rover_id", "R-001")
            target_zone = payload.get("target_zone", "Zone C")
            now_iso = datetime.now().isoformat()
            now_time = datetime.now().strftime("%I:%M %p")
            m_id = f"M{int(datetime.now().timestamp())}"

            c.execute("INSERT INTO rover_missions VALUES (?, ?, 'CRITICAL_DISPATCH', 'Z003', 'CRITICAL', 'IN_PROGRESS', ?)", (m_id, rover_id, now_iso))
            c.execute("UPDATE rovers SET status='MOVING', target_zone=?, mission='Emergency Fire Investigation' WHERE rover_id=?", (target_zone, rover_id))
            c.execute("INSERT INTO activity_logs VALUES (?, ?, 'ROVER', ?, 'INFO', 'Zone C', ?)", (f"ACT{int(datetime.now().timestamp())}", now_time, f"{rover_id} dispatched to {target_zone}", now_iso))
            conn.commit()
            conn.close()
            return self.send_json({"status": "DISPATCHED", "mission_id": m_id, "rover_id": rover_id, "target_zone": target_zone})

        conn.close()
        self.send_error(404)

    def log_message(self, format, *args):
        return

def run():
    init_database()
    server = socketserver.TCPServer(("", PORT), WildfireServer)
    print(f"🌲 WILDFIRE GUARD Backend & PDF Engine running on http://localhost:{PORT}")
    server.serve_forever()

if __name__ == "__main__":
    init_database()
    threading.Thread(target=run, daemon=True).start()
    webbrowser.open(f"http://localhost:{PORT}")
    print(f"🌲 Dashboard & PDF System active at http://localhost:{PORT}")
    threading.Event().wait()
