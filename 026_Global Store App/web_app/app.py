import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import text
import sys
import os
from datetime import datetime, timedelta

# Ensure the project root is in the path to import the pipeline modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.db_connector import SQLServerConnector

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Global Store Manager",
    page_icon="🏪",
    layout="wide"
)

# Custom CSS for a professional look
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e9ecef; }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE CONNECTION ---
@st.cache_resource
def get_db_engine():
    """Initializes and caches the database engine connection."""
    SERVER_NAME = 'localhost' 
    DATABASE_NAME = 'GlobalStoreDB'
    db = SQLServerConnector(SERVER_NAME, DATABASE_NAME)
    return db.get_engine()

engine = get_db_engine()

# --- CACHED DATA FETCHING ---
@st.cache_data(ttl=600)
def fetch_executive_summary(_engine):
    query = """
        SELECT 
            SUM(sales) as total_sales,
            SUM(profit) as total_profit,
            COUNT(order_id) as total_orders,
            COUNT(DISTINCT customer_id) as total_customers
        FROM fact_sales
    """
    return pd.read_sql(query, _engine).iloc[0]

@st.cache_data(ttl=600)
def fetch_sales_trend(_engine):
    query = """
        SELECT CAST(order_date AS DATE) as date, SUM(sales) as sales 
        FROM fact_sales GROUP BY order_date ORDER BY order_date
    """
    df = pd.read_sql(query, _engine)
    df['date'] = pd.to_datetime(df['date'])
    return df.set_index('date').resample('M').sum().reset_index()

@st.cache_data(ttl=600)
def fetch_global_analytics(_engine):
    query = """
    SELECT f.sales, f.profit, l.market, l.country, p.category, f.order_date
    FROM fact_sales f
    JOIN dim_location l ON f.location_key = l.location_key
    JOIN dim_product p ON f.product_id = p.product_id
    """
    return pd.read_sql(query, _engine)

@st.cache_data(ttl=600)
def fetch_product_intelligence(_engine):
    query = """
    SELECT f.sales, f.profit, p.category, p.sub_category 
    FROM fact_sales f 
    JOIN dim_product p ON f.product_id = p.product_id
    """
    return pd.read_sql(query, _engine)

@st.cache_data(ttl=600)
def fetch_customer_loyalty(_engine):
    query = """
    SELECT f.sales, f.profit, c.customer_name, c.segment, f.customer_id, f.order_date, f.order_id
    FROM fact_sales f 
    JOIN dim_customer c ON f.customer_id = c.customer_id
    """
    return pd.read_sql(query, _engine)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🏪 Global Store Admin")
st.sidebar.markdown("---")

try:
    with engine.connect() as conn:
        st.sidebar.success("✅ Gold Layer Connected")
except Exception:
    st.sidebar.error("❌ Database Offline")

menu = st.sidebar.radio(
    "Management Console",
    [
        "Executive Summary", 
        "Global Analytics", 
        "Product Intelligence", 
        "Customer Loyalty",
        "Sales Pulse",
        "Audit Logs"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("Architecture: Medallion (Gold)")

# --- HELPER FUNCTIONS ---
def format_currency(value):
    """Formats large numbers into Millions string."""
    return f"${value / 1_000_000:.2f}M"

# --- MAIN APP LOGIC ---

if menu == "Executive Summary":
    st.title("🚀 Executive Summary")
    st.subheader("High-level business health")

    try:
        df_summary = fetch_executive_summary(engine)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Revenue", format_currency(df_summary['total_sales']))
        m2.metric("Total Profit", format_currency(df_summary['total_profit']))
        m3.metric("Total Orders", f"{int(df_summary['total_orders']):,}")
        
        margin = (df_summary['total_profit'] / df_summary['total_sales'] * 100) if df_summary['total_sales'] != 0 else 0
        m4.metric("Net Profit Margin", f"{margin:.1f}%")

        st.markdown("---")
        
        st.markdown("#### 📈 Sales Momentum")
        df_trend = fetch_sales_trend(engine)
        
        fig = px.area(df_trend, x='date', y='sales', line_shape='spline', color_discrete_sequence=['#3b82f6'])
        fig.update_layout(height=400, margin=dict(t=20, b=20, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Data Error: {e}")

elif menu == "Global Analytics":
    st.title("🌍 Global Market Analytics")
    
    df = fetch_global_analytics(engine)
    
    # KPIs for Global Section
    k1, k2, k3 = st.columns(3)
    k1.metric("Total Countries", f"{df['country'].nunique()}")
    k2.metric("Primary Market", f"{df.groupby('market')['sales'].sum().idxmax()}")
    k3.metric("Avg Sale per Region", f"${df.groupby('market')['sales'].sum().mean() / 1000:.1f}k")

    # Filters
    markets = st.multiselect("Filter Markets", df['market'].unique(), default=df['market'].unique())
    df_filtered = df[df['market'].isin(markets)]

    col_map, col_pie = st.columns([2, 1])
    with col_map:
        st.markdown("#### Sales Distribution by Geography")
        df_geo = df_filtered.groupby('country')['sales'].sum().reset_index()
        fig_map = px.choropleth(df_geo, locations="country", locationmode='country names', color="sales",
                                color_continuous_scale="Viridis", height=500)
        st.plotly_chart(fig_map, use_container_width=True)

    with col_pie:
        st.markdown("#### Market Contribution")
        fig_pie = px.pie(df_filtered, values='sales', names='market', hole=.4)
        st.plotly_chart(fig_pie, use_container_width=True)

elif menu == "Product Intelligence":
    st.title("📦 Product & Category Intelligence")
    
    df_prod = fetch_product_intelligence(engine)

    # KPIs for Product Section
    p1, p2, p3 = st.columns(3)
    p1.metric("Top Category", df_prod.groupby('category')['sales'].sum().idxmax())
    p2.metric("Best Sub-Category", df_prod.groupby('sub_category')['profit'].sum().idxmax())
    p3.metric("Profitability Ratio", f"{(df_prod['profit'].sum() / df_prod['sales'].sum() * 100):.1f}%")

    tab1, tab2 = st.tabs(["Performance Tree", "Sub-Category Analysis"])

    with tab1:
        fig_tree = px.treemap(
            df_prod, 
            path=['category', 'sub_category'], 
            values='sales', 
            color='profit',
            color_continuous_scale='RdYlGn', 
            color_continuous_midpoint=0
        )
        st.plotly_chart(fig_tree, use_container_width=True)

    with tab2:
        df_bar = df_prod.groupby('sub_category')[['sales', 'profit']].sum().sort_values('sales', ascending=False).reset_index()
        fig_bar = px.bar(df_bar, x='sub_category', y=['sales', 'profit'], barmode='group')
        st.plotly_chart(fig_bar, use_container_width=True)

elif menu == "Customer Loyalty":
    st.title("👥 Customer Segmentation & Loyalty")
    
    df_cust = fetch_customer_loyalty(engine)
    df_cust['order_date'] = pd.to_datetime(df_cust['order_date'])
    
    # --- CHURN CALCULATION LOGIC ---
    ref_date = df_cust['order_date'].max()
    cust_behavior = df_cust.groupby('customer_id').agg({
        'order_date': [lambda x: (ref_date - x.max()).days, 'min'],
        'order_id': 'count',
        'sales': 'sum',
        'customer_name': 'first',
        'segment': 'first'
    }).reset_index()
    
    cust_behavior.columns = ['customer_id', 'days_since_last_order', 'first_order_date', 'order_frequency', 'total_spend', 'name', 'segment']
    churn_threshold = 180
    cust_behavior['status'] = cust_behavior['days_since_last_order'].apply(lambda x: 'Churned' if x > churn_threshold else 'Active')
    
    total_cust = len(cust_behavior)
    active_cust = (cust_behavior['status'] == 'Active').sum()
    churn_rate = (total_cust - active_cust) / total_cust * 100
    avg_freq = cust_behavior['order_frequency'].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Base", f"{total_cust:,}")
    c2.metric("Active Base", f"{active_cust:,}")
    c3.metric("Churn Rate", f"{churn_rate:.1f}%", delta=f"-{churn_rate:.1f}%", delta_color="inverse")
    c4.metric("Avg Order Freq", f"{avg_freq:.1f}")

    tab_segments, tab_churn = st.tabs(["Segmentation Analysis", "Retention & Churn Analytics"])

    with tab_segments:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### Sales by Segment")
            fig_seg = px.pie(df_cust, values='sales', names='segment', hole=0.3)
            st.plotly_chart(fig_seg, use_container_width=True)
        
        with col_b:
            st.markdown("#### Top 10 Customers by Revenue")
            top_cust = cust_behavior.nlargest(10, 'total_spend')
            fig_top = px.bar(top_cust, y='name', x='total_spend', orientation='h', color='total_spend')
            fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_top, use_container_width=True)

    with tab_churn:
        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.markdown("#### 🔄 Customer Retention Matrix")
            fig_scatter = px.scatter(
                cust_behavior, 
                x="order_frequency", 
                y="total_spend", 
                color="status",
                size="total_spend",
                hover_data=['name', 'days_since_last_order'],
                color_discrete_map={'Active': '#10b981', 'Churned': '#ef4444'},
                labels={"order_frequency": "Number of Orders", "total_spend": "Total Revenue ($)"}
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
            
        with col_right:
            st.markdown("#### 🚨 At-Risk High-Value Customers")
            at_risk = cust_behavior[cust_behavior['status'] == 'Churned'].nlargest(5, 'total_spend')
            for _, row in at_risk.iterrows():
                st.warning(f"**{row['name']}** \nSpend: ${row['total_spend']:,.0f} | Inactive: {row['days_since_last_order']} days")

elif menu == "Sales Pulse":
    st.title("Sales Performance Analysis")
    st.info("")

    df_sales = fetch_global_analytics(engine)
    df_sales['order_date'] = pd.to_datetime(df_sales['order_date'])
    df_sales['day_of_month'] = df_sales['order_date'].dt.day
    
    # Filter for Day 27
    day_27_data = df_sales[df_sales['day_of_month'] == 27]
    avg_daily_sales = df_sales.groupby(df_sales['order_date'].dt.date)['sales'].sum().mean()
    day_27_avg_sales = day_27_data.groupby(day_27_data['order_date'].dt.date)['sales'].sum().mean()
    
    d1, d2, d3 = st.columns(3)
    d1.metric("Day 27 Avg Sales", f"${day_27_avg_sales:,.2f}")
    d2.metric("Vs. Daily Mean", f"{((day_27_avg_sales/avg_daily_sales - 1)*100):.1f}%", delta_color="normal")
    d3.metric("Total Day 27 Revenue", format_currency(day_27_data['sales'].sum()))

    st.markdown("#### 📈 Historical Performance: Every 'Day 27'")
    day_27_trend = day_27_data.groupby(day_27_data['order_date'].dt.to_period('M'))['sales'].sum().reset_index()
    day_27_trend['order_date'] = day_27_trend['order_date'].astype(str)
    
    fig_day27 = px.line(day_27_trend, x='order_date', y='sales', markers=True, title="Revenue on the 27th of Each Month")
    st.plotly_chart(fig_day27, use_container_width=True)

    col_cat, col_mkt = st.columns(2)
    with col_cat:
        st.markdown("#### Day 27 Category Split")
        fig_cat27 = px.bar(day_27_data.groupby('category')['sales'].sum().reset_index(), x='category', y='sales', color='category')
        st.plotly_chart(fig_cat27, use_container_width=True)
    with col_mkt:
        st.markdown("#### Day 27 Top Markets")
        fig_mkt27 = px.pie(day_27_data.groupby('market')['sales'].sum().reset_index(), values='sales', names='market', hole=0.4)
        st.plotly_chart(fig_mkt27, use_container_width=True)

elif menu == "Audit Logs":
    st.title("📑 Data Audit")
    st.markdown("Review raw transactions from the Gold Layer.")
    
    rows = st.slider("Number of records", 100, 5000, 500)
    @st.cache_data(ttl=300)
    def fetch_audit_logs(_engine, _rows):
        return pd.read_sql(f"SELECT TOP {_rows} * FROM fact_sales ORDER BY order_date DESC", _engine)
        
    df_fact = fetch_audit_logs(engine, rows)
    st.dataframe(df_fact, use_container_width=True)