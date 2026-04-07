import streamlit as st
import pandas as pd
try:
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError:
    st.error("Missing Dependency: Please run 'pip install plotly' in your terminal to enable advanced visualizations.")
    st.stop()
from datetime import datetime
from api_handler import WeatherEngine

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="SkyCast Pro | Meteorological Analytics",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR PROFESSIONAL UI ---
st.markdown("""
    <style>
    /* Main background and font */
    .main { background-color: #f8fafd; font-family: 'Inter', sans-serif; }
    
    /* Custom Card Styling */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e1e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        text-align: center;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e1e8f0;
    }
    
    /* Metric Label refinement */
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        color: #64748b !important;
    }
    
    /* Title styling */
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    
    /* Insight Box */
    .insight-box {
        background: linear-gradient(135deg, #6366f1 0%, #4338ca 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ANALYTICAL LOGIC ---
def generate_data_story(df, current):
    """Crafts a professional narrative based on multi-variate analysis."""
    avg_temp = df['temp'].mean()
    peak_temp = df['tempmax'].max()
    is_windy = df['windspeed'].max() > 25
    rain_risk = df['precipprob'].mean() > 30
    
    story = f"**Current Status:** {current['conditions']} at {current['temp']}°C. "
    
    if rain_risk:
        story += "📊 **Trend Alert:** Our models detect a volatile precipitation pattern. Expect intermittent disruptions to outdoor operations. "
    else:
        story += "📊 **Trend Alert:** Stable atmospheric pressure suggests a consistent clear-sky period ahead. "
        
    if is_windy:
        story += "⚠️ **Operational Risk:** Elevated wind speeds detected (Peak: {0:.1f} km/h). High-altitude or maritime activities may require secondary risk assessments.".format(df['windspeed'].max())
        
    return story

def create_temp_chart(df):
    """Advanced Plotly Range Chart."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['datetime'], y=df['tempmax'],
        line=dict(color='#ef4444', width=3),
        name='Max Temp',
        mode='lines+markers'
    ))
    fig.add_trace(go.Scatter(
        x=df['datetime'], y=df['tempmin'],
        line=dict(color='#3b82f6', width=3),
        name='Min Temp',
        fill='tonexty', # Fills the area between max and min
        fillcolor='rgba(59, 130, 246, 0.1)',
        mode='lines+markers'
    ))
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified"
    )
    return fig

# --- MAIN DASHBOARD INTERFACE ---
st.markdown('<h1 class="main-title">SkyCast Pro Analytics</h1>', unsafe_allow_html=True)
st.write("Meteorological Intelligence System for Hamburg Research & Logistics")

# Sidebar Configuration
with st.sidebar:
    st.image("https://www.visualcrossing.com/assets/img/logo.png", width=150)
    st.header("Parameters")
    city_input = st.text_input("Global Location Filter", "Hamburg, Germany")
    st.divider()
    st.caption("Data Source: Visual Crossing High-Resolution Satellite & Station Network")
    st.info("Current Mode: Metric (Celsius/km/h)")

engine = WeatherEngine()

# Execution Flow
if city_input:
    data = engine.fetch_weather(city_input)
    
    if "error" in data:
        st.error(data["error"])
    else:
        # Data Preparation
        current = data['currentConditions']
        forecast_df = pd.DataFrame(data['days'])
        forecast_df['datetime'] = pd.to_datetime(forecast_df['datetime'])
        
        # --- 1. EXECUTIVE KPIs ---
        st.markdown("### 🔍 Executive Real-Time Snapshot")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Thermal Index", f"{current['temp']}°C", f"{current['feelslike']-current['temp']:.1f}°C Feels")
        with m2:
            st.metric("Aqueous Saturation", f"{current['humidity']}%", "Stable" if current['humidity'] < 70 else "High")
        with m3:
            st.metric("Atmospheric Flux", f"{current['windspeed']} km/h", f"Gusto {current.get('windgust', 0)}")
        with m4:
            st.metric("Optical Range", f"{current['visibility']} km", "Optimal" if current['visibility'] > 10 else "Reduced")

        # --- 2. DATA STORY OVERLAY ---
        st.markdown(f"""
            <div class="insight-box">
                <h3>📢 Intelligence Report: {data['resolvedAddress']}</h3>
                <p>{generate_data_story(forecast_df, current)}</p>
            </div>
            """, unsafe_allow_html=True)

        # --- 3. ANALYTICAL VISUALS ---
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.markdown("#### 🌡️ Temperature Variance & Predicted Range")
            st.plotly_chart(create_temp_chart(forecast_df), use_container_width=True)
            
            st.markdown("#### ☔ Precipitation Intensity Forecast")
            fig_precip = px.bar(forecast_df, x='datetime', y='precipprob', 
                               color='precipprob', color_continuous_scale='Blues',
                               labels={'precipprob': 'Rain Probability %'})
            fig_precip.update_layout(plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
            st.plotly_chart(fig_precip, use_container_width=True)

        with col_right:
            st.markdown("#### ⚖️ Correlation Matrix")
            # Relationship between wind and temp
            fig_corr = px.scatter(forecast_df, x="temp", y="windspeed", 
                                 size="humidity", color="temp",
                                 title="Temp vs Wind correlation",
                                 template="plotly_white")
            st.plotly_chart(fig_corr, use_container_width=True)
            
            st.markdown("#### 🛡️ Readiness Protocol")
            st.checkbox("Logistics Preparedness", value=current['windspeed'] < 30)
            st.checkbox("Outdoor Operations", value=current['precipprob'] < 20)
            st.checkbox("HVAC Optimization", value=abs(current['temp'] - 20) < 10)

        # --- 4. DATA ACCESS ---
        with st.expander("📁 Comprehensive Meteorological Record"):
            st.dataframe(forecast_df, use_container_width=True)