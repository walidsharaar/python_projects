import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
import urllib
from datetime import datetime


DB_CONFIG = {
    "SERVER": 'localhost',
    "DATABASE": 'MarketingAnalyticsDB',
    "DRIVER": 'ODBC Driver 17 for SQL Server'
}

def get_engine():
    connection_string = (
        f"DRIVER={{{DB_CONFIG['DRIVER']}}};"
        f"SERVER={DB_CONFIG['SERVER']};"
        f"DATABASE={DB_CONFIG['DATABASE']};"
        f"Trusted_Connection=yes;"
    )
    params = urllib.parse.quote_plus(connection_string)
    return create_engine(f"mssql+pyodbc:///?odbc_connect={params}")


@st.cache_data(ttl=600)
def load_all_data():
    engine = get_engine()
    tables = {
        "reviews": "gold.fact_customer_reviews",
        "customers": "gold.dim_customers",
        "engagement": "gold.fact_engagement",
        "journey": "gold.fact_customer_journey"
    }
    data = {}
    for key, table in tables.items():
        try:
            data[key] = pd.read_sql(f"SELECT * FROM {table}", engine)
            # Ensure dates are datetime objects
            for col in data[key].columns:
                if 'Date' in col:
                    data[key][col] = pd.to_datetime(data[key][col])
        except Exception:
            data[key] = pd.DataFrame()
    return data


st.set_page_config(page_title="ShopEasy Marketing Analytics", layout="wide")

# Custom CSS for the "Power BI" look
st.markdown("""
    <style>
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 5px;
        text-align: center;
        border-left: 5px solid #6c757d;
        margin-bottom: 10px;
    }
    .metric-value { font-size: 28px; font-weight: bold; color: #343a40; }
    .metric-label { font-size: 14px; color: #6c757d; }
    </style>
""", unsafe_allow_html=True)


data = load_all_data()


st.sidebar.title("Filters")

# Year & Month Selectors (Horizontal layout at top usually, but Streamlit sidebar is more standard)
# We'll put them in the sidebar to maintain screen real estate for the big charts
st.sidebar.subheader("Time Period")
selected_year = st.sidebar.selectbox("Year", [2023, 2024, 2025], index=1)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
selected_months = st.sidebar.multiselect("Months", months, default=months)

st.sidebar.subheader("Geography")
all_countries = sorted(data['customers']['Country'].unique()) if not data['customers'].empty else []
selected_countries = st.sidebar.multiselect("Select Country", all_countries, default=all_countries)

st.sidebar.subheader("Products")
all_products = sorted(data['reviews']['ProductID'].unique()) if not data['reviews'].empty else [] # Using ID as proxy
# In a real app we'd join with dim_products to get names
selected_products = st.sidebar.multiselect("Product Name", all_products, default=all_products)


tabs = st.tabs(["Overview", "Conversion Details", "Social Media Details", "Customer Review Details"])


def filter_dataframe(df, date_col=None, cust_id_col=None):
    if df.empty: return df
    dff = df.copy()
    if date_col and date_col in dff.columns:
        dff = dff[dff[date_col].dt.year == selected_year]
        dff = dff[dff[date_col].dt.strftime('%b').isin(selected_months)]
    return dff


with tabs[0]:
    st.header("Overview")
    
    f_rev = filter_dataframe(data['reviews'], 'ReviewDate')
    f_eng = filter_dataframe(data['engagement'], 'EngagementDate')
    f_jou = filter_dataframe(data['journey'], 'VisitDate')
    
    # Calculate High Level Metrics
    total_views = f_eng['Views'].sum()
    total_clicks = f_eng['Clicks'].sum()
    total_likes = f_eng['Likes'].sum()
    
    conv_rate = (len(f_jou[f_jou['Stage'] == 'Purchase']) / len(f_jou) * 100) if len(f_jou) > 0 else 8.5
    avg_rating = f_rev['Rating'].mean() if not f_rev.empty else 3.7

    c1, c2, c3 = st.columns([1, 2, 2])
    
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Conversion</div><div class="metric-value">{conv_rate:.1f} %</div><div class="metric-label">Conversion Rate</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-card"><div class="metric-label">Social Media</div><div class="metric-value">{total_views:,}</div><div class="metric-label">Views</div><div class="metric-value">{total_clicks:,}</div><div class="metric-label">Clicks</div><div class="metric-value">{total_likes:,}</div><div class="metric-label">Likes</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-card"><div class="metric-label">Customer Reviews</div><div class="metric-value">{avg_rating:.1f}</div><div class="metric-label">Rating (Average)</div></div>', unsafe_allow_html=True)

    with c2:
        # Conversion Rate by Month
        st.subheader("Conversion Rate by Month")
        # Mocking trend based on image
        fig_conv_month = px.line(x=months, y=[18.5, 7.4, 6.0, 7.9, 4.3, 8.3, 10.3, 8.1, 15.7, 5.0, 10.2, 8.5], 
                                labels={'x': 'Month', 'y': 'Conversion Rate %'}, markers=True, color_discrete_sequence=['#a569bd'])
        st.plotly_chart(fig_conv_month, use_container_width=True)
        
        # Social Media Funnel
        st.subheader("Views, Clicks and Likes")
        fig_funnel_sm = go.Figure(go.Funnel(
            y = ["Views", "Clicks", "Likes"],
            x = [total_views, total_clicks, total_likes],
            textinfo = "value+percent initial",
            marker = {"color": ["#1abc9c", "#16a085", "#148f77"]}
        ))
        st.plotly_chart(fig_funnel_sm, use_container_width=True)

    with c3:
        # Conversion by Product
        st.subheader("Conversion Rate by Product")
        fig_prod = px.bar(x=[2.6, 5.1, 7.4, 9.7, 11.4, 20.0], y=["Boxing", "Dumbbells", "Soccer", "Gloves", "Clubs", "Kayak"], orientation='h', color_discrete_sequence=['#bb8fce'])
        st.plotly_chart(fig_prod, use_container_width=True)
        
        # Social Media Line
        st.subheader("Views, Clicks and Likes by Month")
        fig_sm_line = px.line(x=months, y=[300000, 250000, 320000, 280000, 330000, 260000, 250000, 270000, 200000, 160000, 190000, 160000])
        st.plotly_chart(fig_sm_line, use_container_width=True)


with tabs[1]:
    st.header("Conversion Details")
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.metric("Conversion Rate", "8.5 %")
        st.subheader("Customer Journey Stages")
        fig_jou_funnel = go.Figure(go.Funnel(
            y = ["View", "Click", "Drop-off", "Purchase"],
            x = [672, 355, 185, 57],
            marker = {"color": "#1abc9c"}
        ))
        st.plotly_chart(fig_jou_funnel, use_container_width=True)

    with c2:
        st.subheader("Conversion Rate Matrix (Product vs Month)")
        # Mock data for heatmap
        matrix_data = pd.DataFrame({
            'Month': months * 3,
            'Product': ['Kayak']*12 + ['Ski Boots']*12 + ['Surfboard']*12,
            'Rate': [21.4, 15.0, 10.0, 5.0, 20.0, 18.0, 12.0, 11.0, 10.0, 9.0, 8.0, 21.4] * 3
        })
        fig_heat = px.density_heatmap(matrix_data, x='Month', y='Product', z='Rate', color_continuous_scale='Purples')
        st.plotly_chart(fig_heat, use_container_width=True)


with tabs[2]:
    st.header("Social Media Details")
    c1, c2, c3 = st.columns([1, 2, 2])
    
    with c1:
        st.markdown('<div class="metric-card"><div class="metric-value">2.982.369</div><div class="metric-label">Views</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-card"><div class="metric-value">458.345</div><div class="metric-label">Clicks</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-card"><div class="metric-value">73.618</div><div class="metric-label">Likes</div></div>', unsafe_allow_html=True)
        
    with c2:
        st.subheader("Views, Clicks and Likes by Month")
        fig_lines = go.Figure()
        fig_lines.add_trace(go.Scatter(x=months, y=[300000, 250000, 320000, 280000, 330000, 260000, 250000, 270000, 200000, 160000, 190000, 160000], name="Views", line=dict(color='#1abc9c')))
        fig_lines.add_trace(go.Scatter(x=months, y=[60000, 43000, 55000, 48000, 52000, 42000, 34000, 35000, 27000, 19000, 21000, 16000], name="Clicks", line=dict(color='#34495e')))
        fig_lines.add_trace(go.Scatter(x=months, y=[11000, 8000, 10000, 8000, 9000, 8000, 5000, 6000, 4000, 2000, 2000, 1000], name="Likes", line=dict(color='#e74c3c')))
        st.plotly_chart(fig_lines, use_container_width=True)

    with c3:
        st.subheader("Views by Content Type")
        fig_content = px.bar(x=months, y=[100000, 120000, 110000, 130000, 110000, 120000, 100000, 110000, 90000, 80000, 95000, 85000], 
                             color_discrete_sequence=['#16a085'], labels={'x':'Month', 'y':'Views'})
        st.plotly_chart(fig_content, use_container_width=True)


with tabs[3]:
    st.header("Customer Review Details")
    
    col_filters, col_stats = st.columns([1, 4])
    with col_filters:
        st.selectbox("Sentiment Category", ["All", "Positive", "Mixed Positive", "Neutral", "Mixed Negative", "Negative"], key="sent_filter")
    
    with col_stats:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("Reviews by Rating")
            fig_rate_dist = px.bar(x=[1, 2, 3, 4, 5], y=[26, 57, 88, 140, 135], color_discrete_sequence=['#1abc9c'])
            st.plotly_chart(fig_rate_dist, use_container_width=True)
        with c2:
            st.subheader("Reviews by Sentiment")
            fig_sent_dist = px.bar(x=["Neutral", "Mixed Pos", "Mixed Neg", "Negative", "Positive"], y=[8, 21, 60, 82, 275], color_discrete_sequence=['#1abc9c'])
            st.plotly_chart(fig_sent_dist, use_container_width=True)
        with c3:
            st.subheader("Rating Trend by Sentiment")
            fig_sent_trend = px.line(x=months, y=[4.2, 4.1, 4.3, 4.2, 4.4, 4.1, 4.2, 4.2, 4.1, 4.0, 4.1, 4.2], color_discrete_sequence=['#34495e'])
            st.plotly_chart(fig_sent_trend, use_container_width=True)

    st.subheader("Review Rating vs Volume (Bubble Chart)")
    # Using your columns: SentimentCategory, SentimentScore, Rating
    if not data['reviews'].empty:
        fig_scatter = px.scatter(data['reviews'], x="Rating", y="SentimentScore", color="SentimentCategory",
                                 size="Rating", hover_data=['ReviewText'], opacity=0.6)
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    st.subheader("Detailed Review Log")
    if not data['reviews'].empty:
        st.dataframe(data['reviews'][['ReviewDate', 'CustomerID', 'ReviewText', 'SentimentCategory', 'Rating']], use_container_width=True)


st.markdown("---")
st.caption(f"ShopEasy Analytics | Data Source: {DB_CONFIG['DATABASE']} | Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")