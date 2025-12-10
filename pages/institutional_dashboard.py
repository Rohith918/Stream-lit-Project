import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

@st.cache_data
def load_data():
    """Load student data from CSV or return mock data"""
    try:
        df = pd.read_csv("./data/student_performance_dataset.csv")
        if len(df) == 0:
            raise ValueError("CSV is empty")
        return df
    except:
        # Mock data fallback
        return pd.DataFrame({
            'student_id': ['S001', 'S002', 'S003', 'S004', 'S005', 'S006', 'S007', 'S008'],
            'name': ['John Smith', 'Emily Davis', 'Michael Chen', 'Sarah Johnson', 'David Martinez', 'Jessica Williams', 'Alex Brown', 'Lisa Anderson'],
            'major': ['Engineering', 'Business', 'Computer Science', 'Arts', 'Engineering', 'Business', 'Computer Science', 'Arts'],
            'program': ['BSc', 'MSc', 'BSc', 'Diploma', 'BSc', 'MSc', 'BSc', 'Diploma'],
            'prior_gpa': [2.1, 2.4, 2.8, 3.0, 3.2, 3.5, 2.9, 3.1],
            'year': ['Junior', 'Sophomore', 'Senior', 'Junior', 'Senior', 'Junior', 'Sophomore', 'Senior'],
            'graduation_year': [2025, 2026, 2024, 2025, 2024, 2025, 2026, 2024],
            'credits': [78, 65, 110, 95, 120, 88, 72, 105],
            'student_performance': ['Pass', 'Fail', 'Pass', 'Pass', 'Pass', 'Pass', 'Fail', 'Pass']
        })

def compute_kpis(df):
    """Calculate key performance indicators"""
    total_students = len(df)
    at_risk = len(df[df['prior_gpa'] < 2.5]) if 'prior_gpa' in df.columns else 0
    prior_gpa = df['prior_gpa'].mean() if 'prior_gpa' in df.columns and len(df) > 0 else None
    financial_risk = len(df[df['credits'] < 30]) if 'credits' in df.columns else 0

    return {
        'total': total_students,
        'at_risk': at_risk,
        'prior_gpa': prior_gpa,
        'financial_risk': financial_risk
    }

def risk_level_from_gpa(prior_gpa):
    """Determine risk level from prior_gpa"""
    if prior_gpa is None or pd.isna(prior_gpa):
        return "Medium"
    if prior_gpa < 2.5:
        return "High"
    elif prior_gpa < 3.4:
        return "Medium"
    return "Low"

def render(navigate_to):
    """Render Institutional Dashboard"""

    st.markdown("""
    <div class="header-container">
        <div class="header-title">🎓 Student Success Intelligence</div>
        <div class="header-subtitle">Comprehensive Student Analytics Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    # Navigation
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📊 Home", use_container_width=True):
            navigate_to("institutional")
    with col2:
        if st.button("📈 Reports", use_container_width=True):
            navigate_to("reports")
    with col3:
        if st.button("🔔 Alerts", use_container_width=True):
            navigate_to("alerts")
    with col4:
        if st.button("👤 Profile", use_container_width=True):
            navigate_to("profile")

    st.divider()

    # Load data
    df = load_data()
    kpis = compute_kpis(df)

    # KPI Cards
    st.markdown("### Key Performance Indicators")
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        st.markdown(f"""
        <div class="kpi-card navy">
            <div class="kpi-label">Total Students</div>
            <div class="kpi-value">{kpis['total']:,}</div>
            <div class="kpi-subtext">Active enrollment</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_col2:
        st.markdown(f"""
        <div class="kpi-card red">
            <div class="kpi-label">At-Risk Students</div>
            <div class="kpi-value">{kpis['at_risk']}</div>
            <div class="kpi-subtext">Requires intervention</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_col3:
        prior_gpa = f"{kpis['prior_gpa']:.2f}" if kpis['prior_gpa'] is not None else "N/A"
        st.markdown(f"""
        <div class="kpi-card gold">
            <div class="kpi-label">Average GPA</div>
            <div class="kpi-value">{prior_gpa}</div>
            <div class="kpi-subtext">Institutional average</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_col4:
        st.markdown(f"""
        <div class="kpi-card orange">
            <div class="kpi-label">Financial Risk</div>
            <div class="kpi-value">{kpis['financial_risk']}</div>
            <div class="kpi-subtext">Outstanding balances</div>
        </div>
        """, unsafe_allow_html=True)

    # Filters
    st.markdown("### Filters")
    col1, col2, col3 = st.columns([2, 2, 3])

    with col1:
        # Program filter only
        programs = ["All Programs"] + sorted(df['program'].dropna().unique().tolist())
        selected_program = st.selectbox("Program", programs, key="program_filter")

    with col2:
        # Risk filter based on prior_gpa
        risk_levels = ["All Levels", "High", "Medium", "Low"]
        selected_risk = st.selectbox("Risk Level", risk_levels, key="risk_filter")

        # Graduation year range
        if 'graduation_year' in df.columns and not df['graduation_year'].dropna().empty:
            y_min, y_max = int(df['graduation_year'].min()), int(df['graduation_year'].max())
            year_range = st.slider("Graduation Year Range", min_value=y_min, max_value=y_max, value=(y_min, y_max), step=1, key="year_range")
        else:
            year_range = None

    with col3:
        st.write("")
        st.caption("Use the filters to refine the dataset across program, risk level, and graduation year range.")

    st.markdown("---")

    # Apply filters
    df_filtered = df.copy()

    if selected_program != "All Programs":
        df_filtered = df_filtered[df_filtered['program'] == selected_program]

    if selected_risk != "All Levels" and 'prior_gpa' in df_filtered.columns:
        df_filtered['risk_level'] = df_filtered['prior_gpa'].apply(risk_level_from_gpa)
        df_filtered = df_filtered[df_filtered['risk_level'] == selected_risk]

    if year_range and 'graduation_year' in df_filtered.columns:
        yr_min, yr_max = year_range
        df_filtered = df_filtered[(df_filtered['graduation_year'] >= yr_min) & (df_filtered['graduation_year'] <= yr_max)]

    # ===== Charts Row 1 =====
    chart_col1, chart_col2 = st.columns(2)

    # 📈 Retention Trend
    with chart_col1:
        st.markdown("### 📈 Retention Trend (Using Student Performance)")
        if "student_performance" in df_filtered.columns and "program" in df_filtered.columns:
            trend = (
                df_filtered.groupby("program")["student_performance"]
                .apply(lambda x: (x == "Pass").mean() * 100)
                .reset_index()
                .rename(columns={"student_performance": "Pass Rate (%)"})
            )
            if len(trend) > 0:
                fig_trend = px.line(trend, x="program", y="Pass Rate (%)", markers=True,
                                    color_discrete_sequence=["#002855"], height=300)
                fig_trend.update_traces(marker=dict(size=8, color="#F5B700"))
                fig_trend.update_layout(
                    hovermode="x unified",
                    margin=dict(l=0, r=0, t=30, b=0),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Arial", color="#002855"),
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("No data available to compute trend.")
        else:
            st.warning("Required columns missing for retention trend.")

    # 📊 Risk Factor by Program
    with chart_col2:
        st.markdown("### 📊 Risk Factor (Failing Students)")
        if "student_performance" in df_filtered.columns and "program" in df_filtered.columns:
            risk_data = (
                df_filtered[df_filtered["student_performance"] == "Fail"]
                .groupby("program")
                .size()
                .sort_values(ascending=False)
            )
            if len(risk_data) > 0:
                fig_risk_bar = px.bar(x=risk_data.index, y=risk_data.values,
                                      labels={ "x": "Program", "y": "At-Risk Students" },
                                      color_discrete_sequence=["#EF4444"], height=300)
                fig_risk_bar.update_layout(
                    margin=dict(l=0, r=0, t=30, b=0),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Arial", color="#002855"),
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig_risk_bar, use_container_width=True)
            else:
                st.info("No at-risk students found for selected filters.")
        else:
            st.warning("Required columns missing for risk factor chart.")

    # ===== Charts Row 2 =====
    st.markdown("### 🎯 Risk Level Distribution")
    if "student_performance" in df_filtered.columns:
        df_filtered["risk_category"] = df_filtered["student_performance"].map({"Fail": "High", "Pass": "Low"})
        risk_dist = df_filtered["risk_category"].value_counts()

        fig_risk_pie = px.pie(
            values=risk_dist.values,
            names=risk_dist.index,
            color=risk_dist.index,
            color_discrete_map={"High": "#EF4444", "Medium": "#F59E0B", "Low": "#10B981"},
            height=300
        )
        fig_risk_pie.update_layout(
            margin=dict(l=0, r=0, t=30, b=0),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Arial", color="#002855")
        )
        st.plotly_chart(fig_risk_pie, use_container_width=True)

    st.divider()

    # Action Button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("➡️ View Advisor Dashboard", use_container_width=True, key="to_advisor"):
            navigate_to("advisor")
