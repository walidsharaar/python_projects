import streamlit as st
import pandas as pd
import numpy as np
from api_handler import WeatherEngine

# Set Page Styling
st.set_page_config(page_title="SkyCast Pro", page_icon="🌤️", layout="wide")

# Custom CSS for a professional look
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eef2f6; }
    .stAlert { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

def get_weather_insight(df, current):
    """Generates a professional textual analysis of the data trend."""
    temp_trend = "rising" if df['tempmax'].iloc[-1] > df['tempmax'].iloc[0] else "cooling down"
    avg_temp = df['temp'].mean()
    rain_days = df[df['precipprob'] > 50].shape[0]
    
    insight = f"**Executive Summary:** The region is currently experiencing {current['conditions'].lower()}. "
    insight += f"Over the next 15 days, we observe a {temp_trend} trend with an average temperature of {avg_temp:.1f}°C. "
    
    if rain_days > 0:
        insight += f"Precautions are advised for {rain_days} days where precipitation probability exceeds 50%."
    else:
        insight += "Expect stable, dry conditions throughout the forecast period."
    
    return insight

st.title("🌤️ SkyCast Professional Analytics")
st.write("Advanced weather intelligence and predictive data storytelling.")

# Sidebar for Input
with st.sidebar:
    st.header("Control Panel")
    city_input = st.text_input("Target Location", "Hamburg, Germany")
    st.divider()
    st.info("💡 **Analytics Note:** This dashboard uses historical normalization to provide forecast accuracy.")

# Initialize API Engine
engine = WeatherEngine()

# Add a check to run automatically or on button press
if st.button("Generate Analytics Report") or city_input:
    with st.spinner('Synthesizing meteorological data...'):
        data = engine.fetch_weather(city_input)
        
    if "error" in data:
        st.error(data["error"])
    else:
        # --- 1. KEY PERFORMANCE INDICATORS (KPIs) ---
        current = data['currentConditions']
        st.subheader(f"Current Metrics: {data['resolvedAddress']}")
        
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Current Temp", f"{current['temp']}°C", help="Real-time temperature")
        kpi2.metric("Feels Like", f"{current['feelslike']}°C")
        kpi3.metric("UV Index", f"{current['uvindex']}", delta_color="inverse")
        kpi4.metric("Visibility", f"{current['visibility']} km")

        # --- 2. DATA STORY & INSIGHTS ---
        forecast_df = pd.DataFrame(data['days'])
        forecast_df['datetime'] = pd.to_datetime(forecast_df['datetime'])
        
        st.markdown("---")
        st.subheader("📝 Automated Weather Insight")
        st.success(get_weather_insight(forecast_df, current))

        # --- 3. ANALYTICAL CHARTS ---
        tab1, tab2, tab3 = st.tabs(["📈 Temperature Trajectory", "☔ Precipitation Risk", "💧 Humidity & Dew"])

        with tab1:
            st.write("#### Maximum vs Minimum Temperature Variance")
            # We use area chart for a more professional "filled" look for ranges
            chart_data = forecast_df.set_index('datetime')[['tempmax', 'tempmin']]
            st.area_chart(chart_data, color=["#ff4b4b", "#0072f0"])

        with tab2:
            st.write("#### Daily Precipitation Probability (%)")
            # Bar chart is better for discrete daily probability
            st.bar_chart(forecast_df.set_index('datetime')['precipprob'], color="#00d4ff")

        with tab3:
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.write("#### Humidity Levels vs Dew Point")
                st.line_chart(forecast_df.set_index('datetime')[['humidity', 'dew']])
            with col_b:
                st.write("#### Stats Overview")
                st.write(forecast_df[['temp', 'humidity', 'windspeed']].describe())

        # --- 4. RAW DATA REPOSITORY ---
        with st.expander("Explore Full Meteorological Dataset"):
            st.dataframe(
                forecast_df[['datetime', 'tempmax', 'tempmin', 'precipprob', 'windspeed', 'conditions']], 
                use_container_width=True,
                hide_index=True
            )
            st.download_button(
                label="Download CSV Report",
                data=forecast_df.to_csv().encode('utf-8'),
                file_name=f'weather_report_{city_input}.csv',
                mime='text/csv',
            )