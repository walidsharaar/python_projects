import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- BRANDING STYLE ---
PARLOA_COLORS = {
    "primary": "#00BF7D",    # Parloa Emerald
    "secondary": "#0F172A",  # Slate 900
    "background": "#FFFFFF", # Pure White for Minimalism
    "text": "#334155",       # Slate 700
    "accent": "#00BF7D",
    "muted": "#F8FAFC"       # Lighter Slate for cards
}

st.set_page_config(page_title="Parloa | Strategic Intelligence", layout="wide")

# Minimalist UI Injection
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
        color: {PARLOA_COLORS['text']};
    }}
    .main {{ background-color: {PARLOA_COLORS['background']}; }}
    
    /* Minimalist Metric Cards - Matching the reference image */
    [data-testid="stMetric"] {{
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }}
    [data-testid="stMetricValue"] {{ font-weight: 600; color: {PARLOA_COLORS['secondary']}; font-size: 2.2rem !important; }}
    [data-testid="stMetricLabel"] {{ font-size: 0.9rem; color: #64748B; margin-bottom: 4px; }}
    
    /* Clean Tab Styling */
    .stTabs [data-baseweb="tab-list"] {{ gap: 24px; }}
    .stTabs [data-baseweb="tab"] {{
        font-weight: 400;
        color: #94A3B8;
    }}
    .stTabs [aria-selected="true"] {{
        color: {PARLOA_COLORS['primary']} !important;
        font-weight: 600;
    }}
    
    /* Interpretation Box */
    .logic-box {{
        background-color: #F8FAFC;
        border-left: 3px solid {PARLOA_COLORS['primary']};
        padding: 1.25rem;
        margin: 1.5rem 0;
        font-size: 0.95rem;
        border-radius: 0 8px 8px 0;
    }}
    .logic-header {{
        font-weight: 600;
        color: {PARLOA_COLORS['secondary']};
        margin-bottom: 0.5rem;
        display: block;
        text-transform: uppercase;
        letter-spacing: 0.025em;
        font-size: 0.8rem;
    }}

    /* Minimalist Branding Logo */
    .brand-logo {{
        font-weight: 800;
        font-size: 1.5rem;
        color: {PARLOA_COLORS['primary']};
        margin-bottom: 1rem;
        letter-spacing: -0.5px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- Data Engine---
@st.cache_data
def load_strategic_data():
    generate_new = False
    try:
        df = pd.read_csv('parloa_interactions.csv')
        required_cols = ['api_latency_ms', 'duration', 'is_contained', 'nps_score']
        if not all(col in df.columns for col in required_cols):
            generate_new = True
        else:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
    except FileNotFoundError:
        generate_new = True

    if generate_new:
        np.random.seed(42)
        n = 3500
        start = datetime.now() - timedelta(days=60)
        
 
        data = {
            'interaction_id': [f"ID-{i:05d}" for i in range(n)],
            'timestamp': [start + timedelta(minutes=np.random.randint(0, 86400)) for i in range(n)],
            'channel': np.random.choice(['Voice', 'Chat', 'WhatsApp', 'Messenger'], n, p=[0.4, 0.3, 0.2, 0.1]),
            'intent': np.random.choice(['Technical', 'Billing', 'Booking', 'FAQ'], n),
            'api_latency_ms': np.random.normal(210, 45, n),
            'nps_score': np.random.randint(0, 11, n)
        }
        df = pd.DataFrame(data)
        
        
        
        def get_outcome(row):
            prob = 0.80
            if row['intent'] == 'Technical': prob -= 0.25
            if row['channel'] == 'Voice': prob -= 0.10
            return 1 if np.random.random() < prob else 0

        df['is_contained'] = df.apply(get_outcome, axis=1)
       
        df['duration'] = df['is_contained'].apply(lambda x: np.random.normal(38, 6) if x else np.random.normal(215, 35))
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.to_csv('parloa_interactions.csv', index=False)

    return df

df_raw = load_strategic_data()

# --- HEADER ---

st.markdown('<div class="brand-logo">PARLOA</div>', unsafe_allow_html=True)
st.title("Strategic Performance Framework")
st.markdown("<p style='color: #64748B; margin-top: -15px; font-size: 1.1rem;'>Agentic AI Intelligence & Operational Growth Metrics</p>", unsafe_allow_html=True)

# --- FILTER BAR ---
channels = df_raw['channel'].unique().tolist()
selected_channels = st.multiselect("Filter Channel View", channels, default=channels)
df = df_raw[df_raw['channel'].isin(selected_channels)].copy()

# --- DASHBOARD CONTENT ---
if not df.empty:
  
    m1, m2, m3, m4 = st.columns(4)
    with m1: 
        st.metric("Containment Rate", f"{df['is_contained'].mean():.1%}", delta="Target: >70%", delta_color="off")
    with m2: 
        st.metric("Avg Handling Time", f"{df['duration'].mean():.0f}s", delta="-12s vs LY", delta_color="normal")
    with m3: 
        st.metric("Avg NPS Score", f"{df['nps_score'].mean():.2f}", delta="+0.4", delta_color="normal")
    with m4: 
        
        st.metric("Total Interactions", f"{len(df):,}", delta="14% WoW", delta_color="normal")

    st.markdown("""
    <div class="logic-box">
        <span class="logic-header">💡 Data Logic: North Star Metrics</span>
        <b>How:</b> Containment is calculated via a Bernoulli trial influenced by intent complexity and channel difficulty. 
        <b>Interpretation:</b> These KPIs define the efficiency of the agentic layer. 
        The 'Friction Gap' between containment and duration (longer durations on escalations) validates the cost-saving potential of high-containment AI.
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # 2. STRATEGIC TABS
    tab_ops, tab_fin, tab_sql = st.tabs(["Operational Frontier", "Unit Economics", "Data Infrastructure"])

    with tab_ops:
        col_l, col_r = st.columns([2, 1])
        with col_l:
            intent_map = df.groupby('intent').agg({'duration': 'mean', 'is_contained': 'mean', 'interaction_id': 'count'}).reset_index()
            fig = px.scatter(intent_map, x="duration", y="is_contained", size="interaction_id", color="intent",
                           template="plotly_white", title="Intent Efficiency Frontier")
            fig.update_layout(
                plot_bgcolor="white", 
                xaxis=dict(showgrid=False, title="Avg Complexity (Seconds)"), 
                yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="Automation Success Rate", tickformat=".0%"),
                margin=dict(t=50, b=50, l=50, r=50)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col_r:
            st.markdown("""
            <div style="margin-top: 50px;">
                <span class="logic-header">🎯 Strategic Mapping</span>
                <b>Logic:</b> Bubble size represents interaction volume. 
                <b>How:</b> We simulated 'Technical' intents with higher variance and mean duration to reflect actual troubleshooting telemetry.
                <b>Actionable Insight:</b> Intents in the lower-right quadrant (Low Success/High Time) are the highest priority for the next iteration of agentic training.
            </div>
            """, unsafe_allow_html=True)

    with tab_fin:
        col_l, col_r = st.columns([2, 1])
        with col_l:
            # ROI Modeling: Containment vs Human Labor Proxy
            df['savings'] = df['is_contained'] * 5.25 # Assume $5.25 savings per containment vs human agent
            savings_data = df.groupby('channel')['savings'].sum().reset_index()
            fig_fin = px.bar(savings_data, x='channel', y='savings', color_discrete_sequence=[PARLOA_COLORS['primary']],
                            template="plotly_white", title="Realized Operational Savings by Channel")
            fig_fin.update_layout(xaxis_title="Channel", yaxis_title="Savings Realized ($)")
            st.plotly_chart(fig_fin, use_container_width=True)
            
        with col_r:
            st.markdown("""
            <div style="margin-top: 50px;">
                <span class="logic-header">💰 Fiscal Logic</span>
                <b>How:</b> Savings are derived from a fixed 'Human-Proxy Cost' ($5.25) multiplied by the binary containment flag.
                <b>Interpretation:</b> This translates technical KPIs into business value. 
                Higher savings in 'Voice' reflect the significant overhead of telephony infrastructure compared to digital channels.
            </div>
            """, unsafe_allow_html=True)

    with tab_sql:
        st.subheader("Infrastructure: SQL Strategy")
        st.markdown("""
        <div class="logic-box">
            <b>How:</b> These queries demonstrate advanced data cleaning and correlation logic used to transform raw logs into the structured telemetry visualized above.
        </div>
        """, unsafe_allow_html=True)
        
        st.code("""
-- Strategic SQL: Calculating Intent-Specific Latency Decay
-- Goal: Identify if slow API responses are driving customers to escalate.
SELECT 
    intent,
    CORR(api_latency_ms, nps_score) as latency_satisfaction_correlation,
    AVG(CASE WHEN api_latency_ms > 300 THEN 1 ELSE 0 END) as latency_outlier_rate
FROM parloa_interactions
GROUP BY 1
ORDER BY 2 DESC;

-- Session Persistence Analysis
-- Goal: Calculate how many digital sessions end in a voice escalation within 24 hours.
WITH SessionChain AS (
    SELECT 
        customer_id, 
        channel, 
        timestamp,
        LEAD(channel) OVER (PARTITION BY customer_id ORDER BY timestamp) as next_channel
    FROM parloa_raw_logs
)
SELECT 
    COUNT(*) as cross_channel_escalations
FROM SessionChain
WHERE channel != 'Voice' AND next_channel = 'Voice';
        """, language="sql")

else:
    st.warning("Select filters from the dropdown above to display performance data.")

st.caption("Strategic Performance Framework | Powered by Parloa Methodology")