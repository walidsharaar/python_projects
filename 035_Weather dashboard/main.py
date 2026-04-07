import streamlit as st
import pandas as pd
from api_handler import WeatherEngine

# Set Page Styling
st.set_page_config(page_title="SkyCast Pro", page_icon="🌤️", layout="wide")

# Custom CSS for a professional look
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_name=True)

st.title("🌤️ SkyCast Professional")
st.write("Real-time weather analytics and 15-day trends.")

# Sidebar for Input
with st.sidebar:
    st.header("Search Settings")
    city_input = st.text_input("Enter City", "London")
    st.info("Tip: You can enter 'City, Country' for better accuracy.")

# Initialize API Engine
engine = WeatherEngine()

if st.button("Analyze Weather"):
    with st.spinner('Accessing global weather stations...'):
        data = engine.fetch_weather(city_input)
        
    if "error" in data:
        st.error(data["error"])
    else:
        # 1. Current Conditions Row
        current = data['currentConditions']
        st.subheader(f"Current Weather in {data['resolvedAddress']}")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Temperature", f"{current['temp']}°C")
        col2.metric("Humidity", f"{current['humidity']}%")
        col3.metric("Wind Speed", f"{current['windspeed']} km/h")
        col4.metric("Conditions", current['conditions'])

        # 2. Visualizing Trends
        st.divider()
        st.subheader("15-Day Temperature Forecast")
        
        # Convert API data to a Pandas DataFrame for charting
        forecast_df = pd.DataFrame(data['days'])
        forecast_df['datetime'] = pd.to_datetime(forecast_df['datetime'])
        
        # Professional Line Chart
        st.line_chart(data=forecast_df, x="datetime", y=["tempmax", "tempmin"])

        # 3. Detailed Day Breakdown
        with st.expander("View Daily Forecast Data"):
            st.dataframe(forecast_df[['datetime', 'tempmax', 'tempmin', 'precip', 'conditions']], use_container_width=True)