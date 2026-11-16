"""
WILDFIRE GUARD — FastAPI + SQLAlchemy Implementation
To run:
    pip install fastapi uvicorn sqlalchemy pydantic
    uvicorn fastapi_backend:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import datetime

app = FastAPI(
    title="Wildfire Guard REST API",
    description="Backend API for AI-Powered Forest Fire Prevention & Monitoring",
    version="2.0.0"
)

# Enable CORS for Frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas for Telemetry Ingestion
class SensorReadingInput(BaseModel):
    sensor_id: str
    temperature: float
    humidity: float
    smoke: float
    soil_moisture: float

class RoverDispatchInput(BaseModel):
    rover_id: str
    target_zone: str

# 17. GET /api/dashboard
@app.get("/api/dashboard")
def get_dashboard():
    return {
        "system": {
            "name": "WILDFIRE GUARD",
            "status": "ONLINE",
            "last_updated": datetime.datetime.now().isoformat()
        },
        "forest": {
            "name": "Western Forest Zone",
            "total_area_km2": 250,
            "monitored_area_km2": 218,
            "coverage": 87.2
        },
        "summary": {
            "active_sensors": 24,
            "online_sensors": 22,
            "warning_sensors": 2,
            "high_risk_areas": 5,
            "active_rovers": 3,
            "hotspots": 4,
            "critical_hotspots": 2
        },
        "risk": {
            "overall_score": 72,
            "level": "HIGH",
            "critical_zone": "Zone C"
        },
        "alerts": {"critical": 2, "warning": 2},
        "system_health": "OPERATIONAL"
    }

# 3. GET /api/zones
@app.get("/api/zones")
def get_zones():
    return [
        {"zone_id": "Z001", "zone_name": "Zone A", "forest_name": "Western Forest Zone", "area_km2": 50, "latitude": 11.230, "longitude": 76.910, "vegetation_density": "Medium", "risk_level": "Low", "status": "MONITORED"},
        {"zone_id": "Z002", "zone_name": "Zone B", "forest_name": "Western Forest Zone", "area_km2": 50, "latitude": 11.245, "longitude": 76.930, "vegetation_density": "High", "risk_level": "Moderate", "status": "MONITORED"},
        {"zone_id": "Z003", "zone_name": "Zone C", "forest_name": "Western Forest Zone", "area_km2": 50, "latitude": 11.276, "longitude": 76.958, "vegetation_density": "High", "risk_level": "Critical", "status": "CRITICAL"},
        {"zone_id": "Z004", "zone_name": "Zone D", "forest_name": "Western Forest Zone", "area_km2": 50, "latitude": 11.260, "longitude": 76.975, "vegetation_density": "High", "risk_level": "High", "status": "MONITORED"},
        {"zone_id": "Z005", "zone_name": "Zone E", "forest_name": "Western Forest Zone", "area_km2": 50, "latitude": 11.215, "longitude": 76.945, "vegetation_density": "Low", "risk_level": "Low", "status": "MONITORED"}
    ]

# 4. GET /api/sensors
@app.get("/api/sensors")
def get_sensors():
    return [
        {"sensor_id": "S-001", "zone_id": "Z001", "latitude": 11.250, "longitude": 76.920, "battery_percentage": 94, "signal_strength": "Strong", "status": "ONLINE", "temperature_c": 31, "humidity_percent": 62, "smoke_ppm": 12, "soil_moisture_percent": 48},
        {"sensor_id": "S-002", "zone_id": "Z002", "latitude": 11.260, "longitude": 76.930, "battery_percentage": 79, "signal_strength": "Good", "status": "WARNING", "temperature_c": 37, "humidity_percent": 38, "smoke_ppm": 28, "soil_moisture_percent": 31},
        {"sensor_id": "S-003", "zone_id": "Z003", "latitude": 11.276, "longitude": 76.958, "battery_percentage": 87, "signal_strength": "Strong", "status": "CRITICAL", "temperature_c": 42, "humidity_percent": 25, "smoke_ppm": 75, "soil_moisture_percent": 18},
        {"sensor_id": "S-004", "zone_id": "Z004", "latitude": 11.265, "longitude": 76.945, "battery_percentage": 71, "signal_strength": "Good", "status": "HIGH", "temperature_c": 35, "humidity_percent": 41, "smoke_ppm": 34, "soil_moisture_percent": 29},
        {"sensor_id": "S-005", "zone_id": "Z005", "latitude": 11.240, "longitude": 76.910, "battery_percentage": 91, "signal_strength": "Strong", "status": "ONLINE", "temperature_c": 29, "humidity_percent": 68, "smoke_ppm": 8, "soil_moisture_percent": 55}
    ]

# 5. GET /api/sensors/{id}/readings
@app.get("/api/sensors/{sensor_id}/readings")
def get_sensor_readings(sensor_id: str):
    return [
        {"sensor_id": sensor_id, "temperature_c": 31, "humidity_percent": 52, "smoke_ppm": 18, "soil_moisture_percent": 29, "recorded_at": "2026-09-03T08:00:00"},
        {"sensor_id": sensor_id, "temperature_c": 35, "humidity_percent": 43, "smoke_ppm": 29, "soil_moisture_percent": 25, "recorded_at": "2026-09-03T09:00:00"},
        {"sensor_id": sensor_id, "temperature_c": 40, "humidity_percent": 34, "smoke_ppm": 51, "soil_moisture_percent": 21, "recorded_at": "2026-09-03T10:00:00"},
        {"sensor_id": sensor_id, "temperature_c": 42, "humidity_percent": 25, "smoke_ppm": 75, "soil_moisture_percent": 18, "recorded_at": "2026-09-03T10:41:52"}
    ]

# POST /api/sensors/readings (IoT Telemetry ingestion)
@app.post("/api/sensors/readings")
def ingest_reading(reading: SensorReadingInput):
    # Simulated AI Model calculation
    risk_score = 91 if reading.temperature >= 40 else 30
    level = "CRITICAL" if risk_score >= 80 else "LOW"
    return {
        "status": "RECORDED",
        "reading": reading,
        "ai_risk_score": risk_score,
        "risk_level": level
    }

# 6. GET /api/risk-analysis
@app.get("/api/risk-analysis")
def get_risk_analysis():
    return {
        "overall_risk": 72,
        "risk_level": "HIGH",
        "zones": [
            {"zone": "Zone A", "risk_score": 24, "risk_level": "LOW", "temperature": 31, "humidity": 62, "smoke": 12, "fire_probability": 24},
            {"zone": "Zone B", "risk_score": 67, "risk_level": "MEDIUM", "temperature": 37, "humidity": 38, "smoke": 28, "fire_probability": 67},
            {"zone": "Zone C", "risk_score": 91, "risk_level": "CRITICAL", "temperature": 42, "humidity": 25, "smoke": 75, "fire_probability": 91},
            {"zone": "Zone D", "risk_score": 78, "risk_level": "HIGH", "temperature": 35, "humidity": 41, "smoke": 34, "fire_probability": 78},
            {"zone": "Zone E", "risk_score": 18, "risk_level": "LOW", "temperature": 29, "humidity": 68, "smoke": 8, "fire_probability": 18}
        ],
        "zone_c_factors": [
            {"factor": "High Temperature", "severity": "HIGH"},
            {"factor": "Low Humidity", "severity": "HIGH"},
            {"factor": "High Smoke Concentration", "severity": "CRITICAL"},
            {"factor": "Low Soil Moisture", "severity": "HIGH"},
            {"factor": "Dense Vegetation", "severity": "MEDIUM"}
        ]
    }

# 8. GET /api/rovers
@app.get("/api/rovers")
def get_rovers():
    return [
        {"rover_id": "R-001", "status": "MOVING", "battery_percentage": 82, "speed_kmh": 4.5, "current_zone": "Zone B", "target_zone": "Zone C", "distance_to_target_km": 2.4, "mission": "Investigate Critical Risk Area", "camera_status": "ACTIVE", "thermal_sensor_status": "ACTIVE", "gps_status": "CONNECTED", "communication_status": "CONNECTED"},
        {"rover_id": "R-002", "status": "INVESTIGATING", "battery_percentage": 64, "speed_kmh": 0, "current_zone": "Zone C", "target_zone": "Zone C", "mission": "Hotspot Detection", "camera_status": "ACTIVE", "thermal_sensor_status": "ACTIVE", "gps_status": "CONNECTED", "communication_status": "CONNECTED"},
        {"rover_id": "R-003", "status": "MOVING", "battery_percentage": 91, "speed_kmh": 4.2, "current_zone": "Zone D", "target_zone": "Zone D Hotspot", "distance_to_target_km": 1.1, "mission": "Investigate Hotspot", "camera_status": "ACTIVE", "thermal_sensor_status": "ACTIVE", "gps_status": "CONNECTED", "communication_status": "CONNECTED"}
    ]

# POST /api/rovers/dispatch
@app.post("/api/rovers/dispatch")
def dispatch_rover(data: RoverDispatchInput):
    return {
        "status": "DISPATCHED",
        "rover_id": data.rover_id,
        "target_zone": data.target_zone,
        "mission": "Emergency Fire Investigation",
        "timestamp": datetime.datetime.now().isoformat()
    }

# 11. GET /api/hotspots
@app.get("/api/hotspots")
def get_hotspots():
    return [
        {"hotspot_id": "H-001", "zone": "Zone C", "latitude": 11.276, "longitude": 76.958, "temperature": 68, "smoke": 82, "fire_probability": 94, "vegetation_density": "High", "wind_speed_kmh": 18, "detected_by": "R-002", "status": "CRITICAL", "detected_at": "2026-09-03T10:38:24"},
        {"hotspot_id": "H-002", "zone": "Zone C", "latitude": 11.279, "longitude": 76.961, "temperature": 61, "smoke": 71, "fire_probability": 88, "vegetation_density": "High", "wind_speed_kmh": 17, "detected_by": "R-002", "status": "CRITICAL", "detected_at": "2026-09-03T10:39:10"},
        {"hotspot_id": "H-003", "zone": "Zone D", "latitude": 11.265, "longitude": 76.945, "temperature": 51, "smoke": 45, "fire_probability": 72, "vegetation_density": "High", "wind_speed_kmh": 14, "detected_by": "R-003", "status": "WARNING", "detected_at": "2026-09-03T10:35:00"},
        {"hotspot_id": "H-004", "zone": "Zone B", "latitude": 11.260, "longitude": 76.930, "temperature": 47, "smoke": 38, "fire_probability": 61, "vegetation_density": "Medium", "wind_speed_kmh": 12, "detected_by": "S-002", "status": "MONITORING", "detected_at": "2026-09-03T10:30:00"}
    ]

# 12. GET /api/alerts
@app.get("/api/alerts")
def get_alerts():
    return [
        {"alert_id": "A-001", "alert_type": "Potential Fire Detected", "severity": "CRITICAL", "zone": "Zone C", "hotspot_id": "H-001", "temperature": 68, "fire_probability": 94, "message": "Potential Fire Detected in Zone C", "detected_by": "R-002", "timestamp": "2026-09-03T10:38:00", "action_status": "Emergency Response Required", "acknowledged": False},
        {"alert_id": "A-002", "alert_type": "High Temperature Detected", "severity": "WARNING", "zone": "Zone D", "temperature": 51, "fire_probability": 72, "message": "High Temperature Detected in Zone D", "timestamp": "2026-09-03T10:35:00", "action_status": "Monitoring", "acknowledged": False}
    ]

# 13. GET /api/activity
@app.get("/api/activity")
def get_activity():
    return [
        {"activity_id": "ACT001", "time": "10:42 AM", "type": "AI_ANALYSIS", "message": "Risk analysis completed", "severity": "INFO"},
        {"activity_id": "ACT002", "time": "10:41 AM", "type": "SENSOR", "message": "Sensor S-003 reported high smoke level", "severity": "WARNING"},
        {"activity_id": "ACT003", "time": "10:40 AM", "type": "ROVER", "message": "Rover R-002 reached Zone C", "severity": "INFO"},
        {"activity_id": "ACT004", "time": "10:39 AM", "type": "HOTSPOT", "message": "Thermal hotspot detected", "severity": "CRITICAL"},
        {"activity_id": "ACT005", "time": "10:38 AM", "type": "ALERT", "message": "Critical fire alert generated", "severity": "CRITICAL"},
        {"activity_id": "ACT006", "time": "10:36 AM", "type": "AI_ANALYSIS", "message": "AI identified Zone C as critical risk", "severity": "CRITICAL"}
    ]

# 14. GET /api/system-health
@app.get("/api/system-health")
def get_health():
    return {
        "components": [
            {"component": "IoT Sensors", "status": "ONLINE"},
            {"component": "AI Prediction", "status": "ONLINE"},
            {"component": "Rover Network", "status": "ONLINE"},
            {"component": "GPS Tracking", "status": "ONLINE"},
            {"component": "Thermal Detection", "status": "ONLINE"},
            {"component": "Communication", "status": "ONLINE"},
            {"component": "Database", "status": "ONLINE"}
        ],
        "overall_status": "OPERATIONAL"
    }

# 15. GET /api/statistics
@app.get("/api/statistics")
def get_statistics():
    return {
        "forest_name": "Western Forest Zone",
        "total_forest_area_km2": 250,
        "monitored_area_km2": 218,
        "coverage_percentage": 87.2,
        "total_sensors": 24,
        "active_rovers": 3,
        "risk_zones": 12,
        "critical_zones": 2,
        "detected_hotspots": 4
    }

# 16. GET /api/reports
@app.get("/api/reports")
def get_reports():
    return [
# 17. GET /api/history (Unified Historical Data Query)
@app.get("/api/history")
def get_history(date_from: Optional[str] = None, date_to: Optional[str] = None, zone: Optional[str] = None):
    return [
        {"time": "10:41 AM", "type": "Sensor", "zone": "Zone C", "loc": "11.276° N, 76.958° E", "val": "S-003: 42°C, 75 ppm smoke, 18% moist", "status": "Critical"},
        {"time": "10:40 AM", "type": "Rover", "zone": "Zone C", "loc": "11.270° N, 76.950° E", "val": "Rover R-002 (3.2 km/h, 65% batt)", "status": "Active"},
        {"time": "10:39 AM", "type": "Hotspot", "zone": "Zone C", "loc": "11.276° N, 76.958° E", "val": "Hotspot H-001: 68°C (94% fire prob)", "status": "Critical"},
        {"time": "10:38 AM", "type": "Alert", "zone": "Zone C", "loc": "11.276° N, 76.958° E", "val": "Potential Fire Detected by R-002", "status": "Critical"},
        {"time": "10:36 AM", "type": "AI Risk", "zone": "Zone C", "loc": "11.276° N, 76.958° E", "val": "AI Model: 91% Fire Probability", "status": "Critical"},
        {"time": "10:00 AM", "type": "Sensor", "zone": "Zone C", "loc": "11.276° N, 76.958° E", "val": "S-003: 40°C, 51 ppm smoke, 21% moist", "status": "Critical"},
        {"time": "09:00 AM", "type": "Sensor", "zone": "Zone C", "loc": "11.276° N, 76.958° E", "val": "S-003: 35°C, 29 ppm smoke, 25% moist", "status": "Warning"},
        {"time": "08:00 AM", "type": "Sensor", "zone": "Zone C", "loc": "11.276° N, 76.958° E", "val": "S-003: 31°C, 18 ppm smoke, 29% moist", "status": "Normal"}
    ]

# 18. GET /api/history/pdf (PDF File Generation Endpoint)
@app.get("/api/history/pdf")
def download_pdf(zone: str = "Z003", date_from: str = "2026-09-03", date_to: str = "2026-09-03"):
    from fastapi.responses import Response
    # In FastAPI, returns the binary stream with attachment headers
    return Response(
        content=b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f \ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n140\n%%EOF",
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Wildfire_History_{date_from}.pdf"'}
    )
