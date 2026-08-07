from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="Bioprocess & Batch Analytics Intelligence",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS styling
st.markdown(
    """
<style>
    .main-header {
        font-size: 26px;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 14px;
        color: #4B5563;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .stAlert {
        border-radius: 8px;
    }
</style>
""",
    unsafe_allow_html=True,
)



def get_telemetry_data(batch_id_str, temp_bias=0.0, do_drop=False):
    try:
        seed_val = int(batch_id_str.split("-")[-1])
    except (ValueError, IndexError):
        seed_val = 42

    np.random.seed(seed_val)

    time_steps = np.arange(0, 24.25, 0.25)

    temp_curve = (
        32.0
        + 0.5 * np.sin(time_steps / 2)
        + np.random.normal(0, 0.1, len(time_steps))
        + temp_bias
    )
    ph_curve = 5.5 - 0.2 * (time_steps / 24) + np.random.normal(
        0, 0.03, len(time_steps)
    )

    do_base = (
        100.0
        - 70.0 * (1 / (1 + np.exp(-(time_steps - 8) / 2)))
        + np.random.normal(0, 1.2, len(time_steps))
    )
    if do_drop:
        do_base = np.maximum(5.0, do_base - 18.0)

    biomass_growth = 2.0 / (1 + np.exp(-(time_steps - 10) / 3)) * 22.0

    return pd.DataFrame({
        "Time_Hours": time_steps,
        "Temperature_C": np.round(temp_curve, 2),
        "pH": np.round(ph_curve, 2),
        "Dissolved_Oxygen_pct": np.round(do_base, 1),
        "Biomass_Concentration_gL": np.round(biomass_growth, 2),
        "Target_Biomass_Golden": np.round(
            2.0 / (1 + np.exp(-(time_steps - 10) / 3)) * 22.0, 2
        ),
        "Target_DO_Golden": np.round(
            100.0 - 70.0 * (1 / (1 + np.exp(-(time_steps - 8) / 2))), 1
        ),
    })


@st.cache_data
def generate_bioprocess_data():
    """Generates synthetic batch summary data."""
    np.random.seed(42)
    num_batches = 30
    batch_ids = [f"BAT-2026-{100 + i}" for i in range(num_batches)]

    batch_data = []
    start_date = datetime(2026, 7, 1)

    for i, b_id in enumerate(batch_ids):
        b_start = start_date + timedelta(days=i * 0.8)
        fermentation_time_hrs = np.random.normal(24, 1.5)

        glucose_concentration = np.random.normal(180, 5)  # g/L
        avg_temp = np.random.normal(32.0, 0.8)  # °C
        avg_ph = np.random.normal(5.5, 0.15)
        avg_do = np.random.normal(25.0, 3.5)

        is_anomaly = i in [5, 12, 19, 27]
        if is_anomaly:
            avg_temp += np.random.choice([2.5, -2.0])
            avg_do -= 8.0
            yield_x_s = np.random.uniform(0.35, 0.41)
            extraction_recovery = np.random.uniform(72.0, 78.0)
            quality_status = "Out of Spec (OOS)"
        else:
            yield_x_s = np.random.normal(0.48, 0.02)
            extraction_recovery = np.random.normal(88.5, 2.0)
            quality_status = "Released"

        final_biomass = glucose_concentration * yield_x_s * 10
        energy_consumed_kwh = fermentation_time_hrs * np.random.uniform(
            110, 130
        )
        specific_energy = energy_consumed_kwh / (final_biomass + 1e-5)

        batch_data.append({
            "Batch_ID": b_id,
            "Start_Time": b_start,
            "Duration_Hrs": round(fermentation_time_hrs, 2),
            "Glucose_Feed_gL": round(glucose_concentration, 1),
            "Avg_Temp_C": round(avg_temp, 2),
            "Avg_pH": round(avg_ph, 2),
            "Avg_DO_pct": round(avg_do, 1),
            "Biomass_Yield_Yxs": round(yield_x_s, 3),
            "Total_Biomass_kg": round(final_biomass, 1),
            "Extraction_Recovery_pct": round(extraction_recovery, 2),
            "Specific_Energy_kWh_kg": round(specific_energy, 2),
            "Quality_Status": quality_status,
            "Operator_Shift": np.random.choice(
                ["Shift A", "Shift B", "Shift C"]
            ),
        })

    return pd.DataFrame(batch_data)


@st.cache_data
def load_batch_data():
    """Loads online dataset if available, otherwise falls back to synthetic generation."""
    url = "https://raw.githubusercontent.com/repo/bioprocess-data/main/batch_data.csv"
    try:
        df = pd.read_csv(url)
        if not df.empty:
            return df
    except Exception:
        pass
    return generate_bioprocess_data()


df_batches = load_batch_data()


st.sidebar.image(
    "https://www.OL.com/fileadmin/OL/images/OL-logo.svg", width=160
)
st.sidebar.title("Data Process Control")
st.sidebar.markdown(
    "**Plant:** Hamburg Wandsbek \n**Unit:** Bioprocess / Fermentation"
)

st.sidebar.subheader("Filter Batches")
shift_filter = st.sidebar.multiselect(
    "Operator Shift:",
    options=df_batches["Operator_Shift"].unique(),
    default=df_batches["Operator_Shift"].unique(),
)
status_filter = st.sidebar.multiselect(
    "Quality Status:",
    options=df_batches["Quality_Status"].unique(),
    default=df_batches["Quality_Status"].unique(),
)

filtered_df = df_batches[
    (df_batches["Operator_Shift"].isin(shift_filter))
    & (df_batches["Quality_Status"].isin(status_filter))
]

st.sidebar.markdown("---")
st.sidebar.markdown("### Process Engineering Persona")
st.sidebar.info(
    "Designed by **Walid Sharaar** for OL GmbH. Demonstrating SCADA telemetry modeling, continuous improvement (CI), statistical process control (SPC), and cross-departmental analytics."
)


st.markdown(
    '<div class="main-header">OL Fermentation & Extraction Process Intelligence</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-header">Continuous Improvement (CI) Dashboard & Cross-Departmental Troubleshooting Tool</div>',
    unsafe_allow_html=True,
)

# TOP LEVEL KPI CARDS
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

total_batches = len(filtered_df)
released_batches = len(
    filtered_df[filtered_df["Quality_Status"] == "Released"]
)
yield_avg = (
    filtered_df["Biomass_Yield_Yxs"].mean() if total_batches > 0 else 0.0
)
rec_avg = (
    filtered_df["Extraction_Recovery_pct"].mean() if total_batches > 0 else 0.0
)
energy_avg = (
    filtered_df["Specific_Energy_kWh_kg"].mean() if total_batches > 0 else 0.0
)

kpi1.metric(
    "Total Batches Analyzed", f"{total_batches}", f"{released_batches} Released"
)
kpi2.metric(
    "Mean Biomass Yield (Y_X/S)",
    f"{yield_avg:.3f} g/g",
    f"{((yield_avg - 0.45)/0.45)*100:+.1f}% vs Target"
    if total_batches > 0
    else "N/A",
)
kpi3.metric(
    "Downstream Recovery",
    f"{rec_avg:.1f}%",
    f"{rec_avg - 85.0:+.1f}% target diff" if total_batches > 0 else "N/A",
)
kpi4.metric(
    "Avg Specific Energy",
    f"{energy_avg:.2f} kWh/kg",
    "-3.2% vs last month",
    delta_color="inverse",
)
kpi5.metric(
    "Quality Pass Rate",
    f"{(released_batches/(total_batches+1e-5))*100:.1f}%",
    "-3.3% OOS alerts",
)

st.markdown("---")

# MAIN TABS
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Executive & Plant KPIs",
    "🧪 Batch Telemetry & Golden Batch",
    "🔍 Root Cause Troubleshooting",
    "📊 SPC & Process Capability (Cpk)",
])


with tab1:
    st.subheader("Plant Operational & Controlling Metrics")
    col_a, col_b = st.columns([2, 1])

    with col_a:
        fig_yield = px.bar(
            filtered_df,
            x="Batch_ID",
            y="Biomass_Yield_Yxs",
            color="Quality_Status",
            color_discrete_map={
                "Released": "#10B981",
                "Out of Spec (OOS)": "#EF4444",
            },
            title="Biomass Yield (Y_X/S) per Production Batch",
            labels={"Biomass_Yield_Yxs": "Yield Coefficient (g cell / g glucose)"},
        )
        fig_yield.add_hline(
            y=0.45,
            line_dash="dash",
            line_color="orange",
            annotation_text="Target Minimum Yield (0.45)",
        )
        fig_yield.update_layout(xaxis_tickangle=-45, template="plotly_white")
        st.plotly_chart(fig_yield, use_container_width=True)

    with col_b:
        fig_scatter = px.scatter(
            filtered_df,
            x="Specific_Energy_kWh_kg",
            y="Extraction_Recovery_pct",
            color="Quality_Status",
            size="Total_Biomass_kg",
            hover_name="Batch_ID",
            title="Energy Intensity vs Downstream Recovery",
            labels={
                "Specific_Energy_kWh_kg": "Energy Intensity (kWh/kg)",
                "Extraction_Recovery_pct": "Recovery Rate (%)",
            },
        )
        fig_scatter.update_layout(template="plotly_white")
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("""
    **Controlling & Management Insight:** Out-of-Spec batches (red) exhibit a double-loss impact: they consume up to 18% higher specific energy per kg of finished yeast extract while delivering significantly lower downstream recovery rates.
    """)


with tab2:
    st.subheader(
        "Real-Time Bioreactor Sensor Telemetry vs. Golden Batch Benchmark"
    )

    selected_batch = st.selectbox(
        "Select Fermentation Batch for Deep Dive:", df_batches["Batch_ID"].unique()
    )
    batch_info = df_batches[df_batches["Batch_ID"] == selected_batch].iloc[0]

    is_anomaly_batch = batch_info["Quality_Status"] == "Out of Spec (OOS)"

    # Pass selected_batch into get_telemetry_data
    df_telemetry = get_telemetry_data(
        batch_id_str=selected_batch,
        temp_bias=2.2 if is_anomaly_batch else 0.0,
        do_drop=is_anomaly_batch,
    )

    # Display batch header metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.info(f"**Batch Status:** {batch_info['Quality_Status']}")
    m2.info(f"**Operator Shift:** {batch_info['Operator_Shift']}")
    m3.info(f"**Glucose Feed:** {batch_info['Glucose_Feed_gL']} g/L")
    m4.info(f"**Total Biomass:** {batch_info['Total_Biomass_kg']} kg")

    col_t1, col_t2 = st.columns(2)

    with col_t1:
        fig_sensor = go.Figure()
        fig_sensor.add_trace(
            go.Scatter(
                x=df_telemetry["Time_Hours"],
                y=df_telemetry["Temperature_C"],
                name="Temp (°C)",
                line=dict(color="#D97706", width=2),
            )
        )
        fig_sensor.add_trace(
            go.Scatter(
                x=df_telemetry["Time_Hours"],
                y=df_telemetry["Dissolved_Oxygen_pct"],
                name="DO (%)",
                line=dict(color="#2563EB", width=2),
            )
        )
        fig_sensor.add_trace(
            go.Scatter(
                x=df_telemetry["Time_Hours"],
                y=df_telemetry["Target_DO_Golden"],
                name="Golden DO Benchmark",
                line=dict(color="#9CA3AF", dash="dash"),
            )
        )
        fig_sensor.update_layout(
            title="Fermentor Thermal & Aeration Profile",
            xaxis_title="Fermentation Time (Hours)",
            template="plotly_white",
        )
        st.plotly_chart(fig_sensor, use_container_width=True)

    with col_t2:
        fig_bio = go.Figure()
        fig_bio.add_trace(
            go.Scatter(
                x=df_telemetry["Time_Hours"],
                y=df_telemetry["Biomass_Concentration_gL"],
                name="Actual Biomass Growth (g/L)",
                line=dict(color="#10B981", width=3),
            )
        )
        fig_bio.add_trace(
            go.Scatter(
                x=df_telemetry["Time_Hours"],
                y=df_telemetry["Target_Biomass_Golden"],
                name="Golden Batch Trajectory",
                line=dict(color="#4B5563", dash="dot"),
            )
        )
        fig_bio.update_layout(
            title="Biomass Accumulation Trajectory",
            xaxis_title="Fermentation Time (Hours)",
            yaxis_title="Biomass (g/L)",
            template="plotly_white",
        )
        st.plotly_chart(fig_bio, use_container_width=True)

    if is_anomaly_batch:
        st.error(
            "⚠️ **Process Deviation Detected:** Dissolved Oxygen dropped below critical threshold (<15%) at hour 8. Temperature exceeded setpoint by +2.2°C, leading to premature cell lysis and reduced biomass accumulation."
        )


with tab3:
    st.subheader("Cross-Functional Troubleshooting & Feature Correlation")
    st.markdown(
        "Investigating process parameter interactions to identify root causes of yield degradation."
    )

    c1, c2 = st.columns([1, 1])

    with c1:
        numeric_cols = [
            "Avg_Temp_C",
            "Avg_pH",
            "Avg_DO_pct",
            "Biomass_Yield_Yxs",
            "Extraction_Recovery_pct",
            "Specific_Energy_kWh_kg",
        ]
        corr = filtered_df[numeric_cols].corr() if len(filtered_df) > 1 else pd.DataFrame()
        if not corr.empty:
            fig_corr = px.imshow(
                corr,
                text_auto=".2f",
                aspect="auto",
                color_continuous_scale="Blues",
                title="Process Parameter Correlation Matrix",
            )
            fig_corr.update_layout(template="plotly_white")
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("Insufficient filtered data to display correlation matrix.")

    with c2:
        fig_shift = px.box(
            filtered_df,
            x="Operator_Shift",
            y="Biomass_Yield_Yxs",
            color="Operator_Shift",
            points="all",
            title="Biomass Yield Consistency Across Operator Shifts",
        )
        fig_shift.update_layout(template="plotly_white")
        st.plotly_chart(fig_shift, use_container_width=True)

    st.markdown("### Actionable Standard Operating Procedure (SOP) Recommendation")
    st.warning("""
    **Process Engineering Insight:** Strong negative correlation observed between `Avg_Temp_C` elevation and `Biomass_Yield_Yxs`. 
    * **Recommended SOP Update (SOP-BIO-042):** Implement automated cooling water valve override when DO drops below 20% during peak exponential growth phase (Hours 6-12).
    """)


with tab4:
    st.subheader("Statistical Process Control (SPC) & Quality Assurance")

    col_spc1, col_spc2 = st.columns([2, 1])

 
    usl = 92.0  # Upper Spec Limit
    lsl = 80.0  # Lower Spec Limit
    mean_rec = filtered_df["Extraction_Recovery_pct"].mean() if len(filtered_df) > 0 else 0.0
    std_rec = (filtered_df["Extraction_Recovery_pct"].std() if len(filtered_df) > 1 else 0.0) + 1e-5

    cp = (usl - lsl) / (6 * std_rec)
    cpu = (usl - mean_rec) / (3 * std_rec)
    cpl = (mean_rec - lsl) / (3 * std_rec)
    cpk = min(cpu, cpl)

    with col_spc1:
        fig_spc = go.Figure()
        fig_spc.add_trace(
            go.Scatter(
                x=filtered_df["Batch_ID"],
                y=filtered_df["Extraction_Recovery_pct"],
                mode="lines+markers",
                name="Extraction Recovery (%)",
                line=dict(color="#1D4ED8"),
            )
        )
        fig_spc.add_hline(
            y=mean_rec,
            line_color="green",
            annotation_text=f"Mean ({mean_rec:.1f}%)",
        )
        fig_spc.add_hline(
            y=mean_rec + 3 * std_rec,
            line_color="red",
            line_dash="dash",
            annotation_text="UCL (+3σ)",
        )
        fig_spc.add_hline(
            y=mean_rec - 3 * std_rec,
            line_color="red",
            line_dash="dash",
            annotation_text="LCL (-3σ)",
        )
        fig_spc.add_hline(
            y=lsl,
            line_color="black",
            line_dash="dot",
            annotation_text=f"QA Lower Spec ({lsl}%)",
        )
        fig_spc.update_layout(
            title="Individual Control Chart (I-Chart) - Downstream Extraction Recovery Rate",
            xaxis_tickangle=-45,
            template="plotly_white",
        )
        st.plotly_chart(fig_spc, use_container_width=True)

    with col_spc2:
        st.markdown("### Process Capability Summary")
        st.metric("Process Capability (Cp)", f"{cp:.2f}")
        st.metric(
            "Process Capability Index (Cpk)",
            f"{cpk:.2f}",
            delta="Capable (>1.33)" if cpk >= 1.33 else "Action Required (<1.33)",
            delta_color="normal" if cpk >= 1.33 else "inverse",
        )

        st.markdown(rf"""
        **QA & Compliance Metrics:**
        * **Lower Spec Limit (LSL):** {lsl}%
        * **Upper Spec Limit (USL):** {usl}%
        * **Process Mean ($\mu$):** {mean_rec:.2f}%
        * **Standard Deviation ($\sigma$):** {std_rec:.2f}%
        """)

st.markdown("---")
st.caption(
    "Data Process Engineer Case Study Dashboard | Powered by Streamlit & Python"
)