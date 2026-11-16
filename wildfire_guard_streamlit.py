"""
WILDFIRE GUARD — Streamlit Frontend Implementation
To run:
    pip install streamlit
    streamlit run wildfire_guard_streamlit.py
"""

import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="WILDFIRE GUARD — AI Forest Fire Prevention",
    page_icon="🌲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Command Center aesthetics
st.markdown("""
<style>
    .metric-card {
        background-color: #15202B;
        border: 1px solid #1F2E3E;
        padding: 16px;
        border-radius: 10px;
        margin-bottom: 12px;
    }
    .critical-banner {
        background: linear-gradient(90deg, rgba(239, 68, 68, 0.25) 0%, rgba(239, 68, 68, 0.08) 100%);
        border-left: 6px solid #EF4444;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 20px;
    }
    .badge-critical { color: #EF4444; font-weight: bold; }
    .badge-warning { color: #F59E0B; font-weight: bold; }
    .badge-normal { color: #10B981; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# 1. HEADER DATA
st.title("🌲 WILDFIRE GUARD")
st.caption("AI-Powered Forest Fire Prevention & Monitoring | ● SYSTEM ONLINE | Last Updated: 10:42:18 AM")

# 14. ALERT DATA (Critical Banner)
st.markdown("""
<div class="critical-banner">
    <h4 style="color:#EF4444; margin:0;">🔴 CRITICAL ALERT: Potential Fire Detected in Zone C (Hotspot H-001)</h4>
    <p style="margin: 4px 0 0 0; color: #D1D5DB; font-size: 13px;">
        Temperature: <strong>68°C</strong> | Fire Probability: <strong>94%</strong> | Detected By: <strong>Rover R-002</strong> (10:38 AM)
    </p>
</div>
""", unsafe_allow_html=True)

# 2. NAVIGATION DATA (Sidebar)
with st.sidebar:
    st.header("Navigation")
    nav_selection = st.radio(
        "Select Module:",
        [
            "Dashboard", "Forest Map", "Sensor Monitoring", "Risk Analysis",
            "Rover Monitoring", "Hotspot Detection", "Alerts", "Reports", "Settings"
        ]
    )
    
    st.divider()
    # 17. SYSTEM HEALTH DATA
    st.subheader("System Health")
    health_data = {
        "Component": ["IoT Sensors", "AI Prediction", "Rover Network", "GPS Tracking", "Thermal Detection", "Communication", "Database"],
        "Status": ["● ONLINE"] * 7
    }
    st.dataframe(pd.DataFrame(health_data), use_container_width=True, hide_index=True)
    st.success("Overall System Status: ● OPERATIONAL")

# 3. DASHBOARD DATA
st.subheader("Forest Fire Monitoring Dashboard")
st.caption("Real-time environmental monitoring and autonomous wildfire prevention")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Active Sensors", "24", "22 Online | 2 Warning")
with col2:
    st.metric("High Risk Areas", "05", "2 Critical | 3 High Risk", delta_color="inverse")
with col3:
    st.metric("Active Rovers", "03", "2 Moving | 1 Investigating")
with col4:
    st.metric("Hotspots", "04", "2 Critical | 2 Under Review", delta_color="inverse")

st.divider()

# 4. FOREST MAP DATA & 9. AI PREDICTION DATA
m_col1, m_col2 = st.columns([2, 1])

with m_col1:
    st.subheader("Western Forest Zone Map (Total Area: 250 km²)")
    map_df = pd.DataFrame([
        {"Zone": "Zone A", "lat": 11.230, "lon": 76.910, "Risk": "Low Risk (🟢)"},
        {"Zone": "Zone B", "lat": 11.245, "lon": 76.930, "Risk": "Moderate Risk (🟡)"},
        {"Zone": "Zone C", "lat": 11.276, "lon": 76.958, "Risk": "Critical Risk (🔴)"},
        {"Zone": "Zone D", "lat": 11.260, "lon": 76.975, "Risk": "High Risk (🟠)"},
        {"Zone": "Zone E", "lat": 11.215, "lon": 76.945, "Risk": "Low Risk (🟢)"}
    ])
    st.map(map_df, latitude="lat", longitude="lon", size=30)
    st.caption("Objects: 📡 Sensor | 🚙 Rover | 🔥 Hotspot | Filters: All, Sensors, Risk Areas, Rovers, Hotspots")

with m_col2:
    # 8 & 9. AI RISK & PREDICTION
    st.subheader("AI Fire Risk Analysis")
    st.metric("Overall Forest Risk", "72%", "HIGH RISK", delta_color="inverse")
    st.markdown("**Prediction for Zone C:** Fire Probability: **91%**")
    st.write("Identified Risk Factors:")
    st.markdown("""
    - ⚠️ High Temperature (42°C)
    - ⚠️ Low Humidity (25%)
    - ⚠️ High Smoke Concentration (75 ppm)
    - ⚠️ Low Soil Moisture (18%)
    - ⚠️ Dense Vegetation
    """)
    st.warning("Recommendation: Deploy Rover R-001 for immediate investigation.")
    if st.button("🚀 DISPATCH ROVER R-001"):
        st.success("Rover R-001 dispatched to Zone C!")

st.divider()

# 5. SENSOR DATA & 6. SENSOR DETAIL DATA
s_col1, s_col2 = st.columns([3, 2])
with s_col1:
    st.subheader("Sensor Monitoring Table")
    sensor_df = pd.DataFrame([
        {"Sensor ID": "S-001", "Zone": "Zone A", "Temperature": "31°C", "Humidity": "62%", "Smoke": "12 ppm", "Soil Moisture": "48%", "Status": "🟢 Normal"},
        {"Sensor ID": "S-002", "Zone": "Zone B", "Temperature": "37°C", "Humidity": "38%", "Smoke": "28 ppm", "Soil Moisture": "31%", "Status": "🟡 Warning"},
        {"Sensor ID": "S-003", "Zone": "Zone C", "Temperature": "42°C", "Humidity": "25%", "Smoke": "75 ppm", "Soil Moisture": "18%", "Status": "🔴 Critical"},
        {"Sensor ID": "S-004", "Zone": "Zone D", "Temperature": "35°C", "Humidity": "41%", "Smoke": "34 ppm", "Soil Moisture": "29%", "Status": "🟠 High"},
        {"Sensor ID": "S-005", "Zone": "Zone E", "Temperature": "29°C", "Humidity": "68%", "Smoke": "8 ppm", "Soil Moisture": "55%", "Status": "🟢 Normal"}
    ])
    st.dataframe(sensor_df, use_container_width=True, hide_index=True)

with s_col2:
    st.subheader("Sensor Detail: S-003 (🔴 Critical)")
    st.markdown("""
    - **Location:** 11.276° N, 76.958° E
    - **Temperature:** 42°C | **Humidity:** 25%
    - **Smoke Level:** 75 ppm | **Soil Moisture:** 18%
    - **Battery:** 87% | **Signal:** Strong
    - **Last Updated:** 10:41:52 AM
    """)
    # 7. Environmental Data
    st.caption("Environmental Dynamics (8 AM - 11 AM)")
    temp_trend = pd.DataFrame({
        "Time": ["8 AM", "9 AM", "10 AM", "11 AM"],
        "Temp (°C)": [25, 30, 35, 42]
    }).set_index("Time")
    st.line_chart(temp_trend)

st.divider()

# 10 & 11. ROVER DATA & LOCATION
st.subheader("Rover Fleet Operations & Telemetry")
r1, r2, r3 = st.columns(3)
with r1:
    st.markdown("### Rover R-001 (MOVING 🚙)")
    st.write("Battery: 82% | Speed: 4.5 km/h")
    st.progress(82)
    st.write("**Current Zone:** Zone B → **Target:** Zone C (2.4 km)")
    st.caption("Mission: Investigate Critical Risk Area | ETA: 32 min")
    st.caption("Navigation: ● Active | GPS: ● Connected | Camera: ● Active | Thermal: ● Active")

with r2:
    st.markdown("### Rover R-002 (INVESTIGATING 🔍)")
    st.write("Battery: 64% | Camera: Active | Thermal: Active")
    st.progress(64)
    st.write("**Current Zone:** Zone C")
    st.caption("Mission: Hotspot Detection")

with r3:
    st.markdown("### Rover R-003 (MOVING 🚙)")
    st.write("Battery: 91% | Speed: 5.2 km/h")
    st.progress(91)
    st.write("**Current Zone:** Zone D → **Target:** Hotspot (1.1 km)")
    st.caption("Mission: Perimeter Patrol")

st.divider()

# 12 & 13. HOTSPOT DATA & DETAIL
h_col1, h_col2 = st.columns(2)
with h_col1:
    st.subheader("Hotspot Detection Registry")
    hotspots_df = pd.DataFrame([
        {"Hotspot": "H-001", "Zone": "Zone C", "Temp": "68°C", "Smoke": "82 ppm", "Probability": "94%", "Status": "🔴 Critical"},
        {"Hotspot": "H-002", "Zone": "Zone C", "Temp": "61°C", "Smoke": "71 ppm", "Probability": "88%", "Status": "🔴 Critical"},
        {"Hotspot": "H-003", "Zone": "Zone D", "Temp": "51°C", "Smoke": "45 ppm", "Probability": "72%", "Status": "🟠 Warning"},
        {"Hotspot": "H-004", "Zone": "Zone B", "Temp": "47°C", "Smoke": "38 ppm", "Probability": "61%", "Status": "🟡 Monitoring"}
    ])
    st.dataframe(hotspots_df, use_container_width=True, hide_index=True)

with h_col2:
    st.subheader("Hotspot Detail: H-001")
    st.error("🚨 EMERGENCY RESPONSE REQUIRED")
    st.markdown("""
    - **Location:** 11.276° N, 76.958° E | **Detected By:** Rover R-002 (10:38:24 AM)
    - **Temperature:** 68°C | **Smoke Level:** 82 ppm | **Fire Probability:** 94%
    - **Vegetation Density:** High | **Wind Speed:** 18 km/h
    - **Action Status:** ✓ Hotspot Detected | ✓ Rover Confirmed | ✓ Location Recorded | ✓ Alert Generated
    """)

st.divider()

# 15 & 16. SYSTEM ACTIVITY & FOREST STATISTICS
act_col, stat_col = st.columns([1, 1])
with act_col:
    st.subheader("⏱️ System Activity Timeline")
    activities = [
        "10:42 AM — ✓ Risk analysis completed",
        "10:41 AM — 📡 Sensor S-003 reported high smoke level",
        "10:40 AM — 🚙 Rover R-002 reached Zone C",
        "10:39 AM — 🔥 Thermal hotspot detected",
        "10:38 AM — 🚨 Critical fire alert generated",
        "10:36 AM — 🤖 AI identified Zone C as critical risk"
    ]
    for act in activities:
        st.write(act)

with stat_col:
    st.subheader("📊 Forest Statistics")
    stats_df = pd.DataFrame([
        {"Data": "Total Forest Area", "Value": "250 km²"},
        {"Data": "Monitored Area", "Value": "218 km²"},
        {"Data": "Coverage", "Value": "87.2%"},
        {"Data": "Total Sensors", "Value": "24"},
        {"Data": "Active Rovers", "Value": "3"},
        {"Data": "Risk Zones", "Value": "12"},
        {"Data": "Critical Zones", "Value": "2"},
        {"Data": "Detected Hotspots", "Value": "4"}
    ])
    st.dataframe(stats_df, use_container_width=True, hide_index=True)
