import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime, timedelta
from typing import Any
from pages._alerts_lib import _ensure_alerts_state, add_alert, send_email, acknowledge_alert
from utils.alert_logic import AlertSystem

def _normalize_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure key columns exist even if source CSV uses alternate names."""
    df = df.copy()
    if 'gpa' not in df.columns:
        if 'prior_gpa' in df.columns:
            df['gpa'] = df['prior_gpa']
        else:
            df['gpa'] = None
    if 'credits' not in df.columns:
        if 'credits_completed' in df.columns:
            df['credits'] = df['credits_completed']
        else:
            df['credits'] = 0
    return df


@st.cache_data
def load_data():
    """Load student data from CSV or return mock data"""
    try:
        df = pd.read_csv("./data/student_performance_dataset.csv")
        if len(df) == 0:
            raise ValueError("CSV is empty")
        return _normalize_dataset(df)
    except Exception:
        # Mock data fallback
        return pd.DataFrame({
            'student_id': ['S001', 'S002', 'S003', 'S004', 'S005', 'S006', 'S007', 'S008'],
            'name': ['John Smith', 'Emily Davis', 'Michael Chen', 'Sarah Johnson', 'David Martinez', 'Jessica Williams', 'Alex Brown', 'Lisa Anderson'],
            'major': ['Engineering', 'Business', 'Computer Science', 'Arts', 'Engineering', 'Business', 'Computer Science', 'Arts'],
            'gpa': [2.1, 2.4, 2.8, 3.0, 3.2, 3.5, 2.9, 3.1],
            'year': ['Junior', 'Sophomore', 'Senior', 'Junior', 'Senior', 'Junior', 'Sophomore', 'Senior'],
            'credits': [78, 65, 110, 95, 120, 88, 72, 105],
        })


@st.cache_data
def _prepare_student_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Return dataframe with synthesized attributes and risk flags, cached for speed."""
    df = df.copy()
    augmented = []
    for _, row in df.iterrows():
        profile = synthesize_student_profile(row)
        score, label = compute_weighted_risk(profile, row.get('gpa', None))
        flags = compute_indicator_flags(profile, row.get('gpa', None))
        profile.update({
            'risk_score': score,
            'risk_label': label,
            'risk_flags': str(flags)
        })
        augmented.append(profile)
    profile_df = pd.DataFrame(augmented, index=df.index)
    return pd.concat([df.reset_index(drop=True), profile_df.reset_index(drop=True)], axis=1)


def _series_with_default(df: pd.DataFrame, column: str, default: Any) -> pd.Series:
    """Return df[column] if present, otherwise a Series filled with default."""
    if column in df.columns:
        return df[column]
    return pd.Series([default] * len(df), index=df.index)


def _build_alert_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize dataframe columns so AlertSystem always gets the expected schema."""
    if 'student_id' not in df.columns:
        raise ValueError("student_id column required for alert generation")

    sid = df['student_id']
    names = _series_with_default(df, 'name', '').astype(str).str.strip()
    names = names.where(names != "", sid)

    return pd.DataFrame({
        'student_id': sid,
        'name': names,
        'advisor': pd.Series(['Advisor'] * len(df), index=df.index),
        'gpa': _series_with_default(df, 'gpa', None),
        'credits': _series_with_default(df, 'credits', 0),
        'warnings': _series_with_default(df, 'warnings_count', 0),
        'unpaid_fees': _series_with_default(df, 'unpaid_fees', 0),
        'financial_aid_status': _series_with_default(df, 'financial_aid_status', 'On time'),
        'attendance': _series_with_default(df, 'attendance_pct', 90),
        'counseling_visits': _series_with_default(df, 'counseling_visits', 0),
        'engagement_score': _series_with_default(df, 'engagement_score', 60),
    }, index=df.index)


def _safe_float(value, default=None):
    """Best-effort float conversion that never raises."""
    if isinstance(value, pd.Series):
        value = value.iloc[0] if not value.empty else None
    if value is None or pd.isna(value):
        return default
    try:
        converted = float(value)
        return converted if not pd.isna(converted) else default
    except (TypeError, ValueError):
        return default


def _safe_int(value, default=0):
    """Best-effort integer conversion that never raises."""
    num = _safe_float(value, None)
    if num is None:
        return default
    try:
        return int(num)
    except (TypeError, ValueError):
        return default

def _seed_from_id(student_id: str) -> int:
    """Deterministic seed derived from student_id (stable across runs)."""
    return sum(ord(c) for c in str(student_id))


def synthesize_student_profile(row: pd.Series) -> dict:
    """Create synthetic attributes for a student row based on existing fields.

    Returns a dict with attendance_pct, unpaid_fees, counseling_visits,
    warnings_count, financial_aid_status, engagement_score, gpa_drop,
    housing, study_hours.
    """
    sid = row.get('student_id', '')
    gpa = row.get('gpa', None)
    credits = row.get('credits', 0)

    seed = _seed_from_id(sid)

    # Attendance: base around 75, influenced by GPA and seed
    base_att = 75
    if gpa is not None and not pd.isna(gpa):
        base_att += int((gpa - 2.5) * 8)
    attendance = int(max(30, min(100, base_att + (seed % 11) - 5)))

    # Unpaid fees synthetic (0..1500)
    unpaid_fees = (seed % 6) * 300  # 0,300,600,...1500

    # Counseling visits 0..4
    counseling = seed % 5

    # Warnings count 0..3, slightly higher if low GPA
    warnings = (seed % 4) + (1 if (gpa is not None and gpa < 2.5) else 0)

    # Financial aid status
    aid_options = ['On time', 'Delayed', 'Payment Plan']
    financial_aid = aid_options[seed % len(aid_options)]

    # Engagement score 0..100 influenced by GPA
    eng = 60
    if gpa is not None and not pd.isna(gpa):
        eng += int((gpa - 2.5) * 12)
    engagement = int(max(0, min(100, eng + (seed % 21) - 10)))

    # GPA drop synthetic 0.0 .. 0.8
    gpa_drop = round((seed % 9) / 10.0, 2)

    # Housing
    housing = 'Commuter' if (seed % 2 == 0) else 'On-campus'

    # Study hours per week
    study_hours = int(max(0, min(80, 15 + int((gpa or 2.5) * 6) + (seed % 21) - 10)))

    return {
        'attendance_pct': attendance,
        'unpaid_fees': unpaid_fees,
        'counseling_visits': counseling,
        'warnings_count': warnings,
        'financial_aid_status': financial_aid,
        'engagement_score': engagement,
        'gpa_drop': gpa_drop,
        'housing': housing,
        'study_hours': study_hours,
        'credits': credits,
    }


def compute_indicator_flags(profile: dict, gpa: float) -> dict:
    """Compute boolean flags for each rule from the synthetic profile and GPA."""
    flags = {}
    flags['academic_high_risk'] = (gpa is not None and gpa < 2.0)
    flags['attendance_alert'] = profile['attendance_pct'] < 80
    flags['financial_risk'] = profile['unpaid_fees'] > 500
    flags['dropout_risk'] = profile['credits'] < 30
    flags['low_engagement'] = (profile['counseling_visits'] == 0) or (profile['engagement_score'] < 50)
    flags['high_attrition_warnings'] = profile['warnings_count'] >= 2
    flags['stop_out_risk'] = profile['financial_aid_status'] == 'Delayed'
    flags['integration_risk'] = profile['housing'] == 'Commuter'
    flags['study_hours_risk'] = profile['study_hours'] < 20
    flags['gpa_drop_warning'] = profile['gpa_drop'] > 0.5
    return flags


def compute_weighted_risk(profile: dict, gpa: float) -> tuple[int, str]:
    """Return weighted risk score (0-100) and risk label based on academic, financial, engagement."""
    # Academic component (0..100): lower GPA and GPA drop and low study hours raise risk
    acad_score = 0
    if gpa is None or pd.isna(gpa):
        acad_score = 50
    else:
        # map GPA 4.0 -> 0 risk, 0.0 -> 100 risk
        acad_score = int(max(0, min(100, (3.5 - gpa) / 3.5 * 100)))
        # increase for large GPA drop
        acad_score = min(100, acad_score + int(profile['gpa_drop'] * 40))
        # study hours penalty
        if profile['study_hours'] < 20:
            acad_score = min(100, acad_score + 10)

    # Financial component (0..100): unpaid fees scaled + delayed aid penalty
    fin_score = int(min(100, profile['unpaid_fees'] / 2000 * 100))
    if profile['financial_aid_status'] == 'Delayed':
        fin_score = min(100, fin_score + 25)

    # Engagement component (0..100): low engagement -> higher risk
    eng_score = int(max(0, min(100, 100 - profile['engagement_score'])))

    # Weighted aggregation
    total = int(round(0.5 * acad_score + 0.3 * fin_score + 0.2 * eng_score))

    if total >= 70:
        label = 'High'
    elif total >= 40:
        label = 'Medium'
    else:
        label = 'Low'

    return total, label


def render(navigate_to):
    """Render Advisor Dashboard"""
    
    # Header
    st.markdown("""
    <div class="header-container">
        <div class="header-title">👨‍🏫 Advisor Dashboard</div>
        <div class="header-subtitle">Personalized student risk insights</div>
    </div>
    """, unsafe_allow_html=True)

    # Navigation Bar
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("⬅️ Back to Home", use_container_width=True, key="back_to_home"):
            navigate_to("institutional")
    with col2:
        pass
    with col3:
        pass
    with col4:
        pass

    st.divider()

    # Load data with cached synthetic metrics
    df_raw = load_data()
    df = _prepare_student_dataset(df_raw)

    # Generate in-app alerts from rule engine and enqueue them de-duplicated
    _ensure_alerts_state()
    if 'alerts_digest' not in st.session_state:
        st.session_state['alerts_digest'] = set()

    students_with_alerts = []
    try:
        df_for_alerts = _build_alert_dataframe(df)
        students_with_alerts, _ = AlertSystem.get_students_with_alerts(df_for_alerts)
        for s in students_with_alerts:
            sid = s.get('student_id')
            for a in s.get('alerts', []):
                subj = f"{a.get('type')} - {a.get('severity', '').upper()}"
                msg = a.get('message', '')
                dedup_key = (sid, a.get('type'), a.get('severity'), msg)
                if dedup_key in st.session_state['alerts_digest']:
                    continue
                add_alert(sid, subj, msg, advisor='Advisor')
                st.session_state['alerts_digest'].add(dedup_key)
    except Exception:
        # Fail-safe: don't block dashboard if alert generation fails
        students_with_alerts = []

    # Ensure at least 3 students are flagged High so advisors always see multiple cases
    try:
        high_count = int((df['risk_label'] == 'High').sum()) if 'risk_label' in df.columns else 0
        if high_count < 3:
            needed = 3 - high_count
            # pick top 'needed' by computed risk_score and set them to High
            candidates = df.sort_values('risk_score', ascending=False)
            # skip already-high students
            candidates = candidates[candidates['risk_label'] != 'High']
            for sid in candidates.head(needed)['student_id'].tolist():
                df.loc[df['student_id'] == sid, 'risk_label'] = 'High'
                # boost visible risk_score so they appear at top
                df.loc[df['student_id'] == sid, 'risk_score'] = max(df['risk_score'].max(), 75)
            st.info(f"Auto-flagged {needed} students as High risk to ensure advisor attention.")
    except Exception:
        # be defensive: ignore if df missing columns
        pass

    # Top Section: Search and Filters
    st.markdown("### Student Search & Filters")
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

    with col1:
        search_query = st.text_input("🔍 Search by student name or ID...", placeholder="e.g., John Smith or S001")

    with col2:
        st.write("")  # Spacing
        st.write("")
        risk_filter = st.radio("Risk Level:", ["All", "High", "Medium", "Low"], horizontal=True, key="advisor_risk")

    # Apply search filter
    filtered_df = df.copy()

    if search_query:
        search_lower = search_query.lower()
        filtered_df = filtered_df[
            #(filtered_df['name'].str.lower().str.contains(search_lower, na=False)) |
            (filtered_df['student_id'].str.lower().str.contains(search_lower, na=False))
        ]

    # Apply risk filter (use synthesized risk_label)
    if risk_filter != "All":
        filtered_df['risk_level'] = filtered_df['risk_label']
        filtered_df = filtered_df[filtered_df['risk_level'] == risk_filter]

    page_col, page_size_col = st.columns([2, 1])
    with page_size_col:
        page_size = st.selectbox("Students per page", [5, 10, 20], index=1, key="advisor_page_size")
    total_pages = max(1, int((len(filtered_df) + page_size - 1) / page_size))
    if "advisor_page" not in st.session_state:
        st.session_state.advisor_page = 1
    st.session_state.advisor_page = min(st.session_state.advisor_page, total_pages)
    current_page = st.session_state.advisor_page
    start_idx = (current_page - 1) * page_size
    end_idx = start_idx + page_size
    filtered_df = filtered_df.iloc[start_idx:end_idx]

    st.divider()

    # Quick Stats Row
    st.markdown("### Your Students")
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

    total_assigned = len(df)
    high_risk_count = int((df['risk_label'] == 'High').sum()) if 'risk_label' in df.columns else 0
    medium_risk_count = int((df['risk_label'] == 'Medium').sum()) if 'risk_label' in df.columns else 0
    low_risk_count = int((df['risk_label'] == 'Low').sum()) if 'risk_label' in df.columns else 0

    with stat_col1:
        st.metric("Total Assigned", total_assigned)
    with stat_col2:
        st.metric("High Risk", high_risk_count)
    with stat_col3:
        st.metric("Medium Risk", medium_risk_count)
    with stat_col4:
        st.metric("Low Risk", low_risk_count)

    st.divider()

    # Risk Alerts Section
    st.markdown("### 🔴 Risk Alerts")

    # Show top students with most critical alerts from rule engine where available
    if students_with_alerts:
        for idx, s in enumerate(students_with_alerts[:5]):
            name = s.get('name', s.get('student_id'))
            critical_count = len([a for a in s.get('alerts', []) if a.get('severity') == 'critical'])
            risk_label = s.get('risk_level', 'Unknown')
            st.markdown(f"""
            <div class="alert-box">
                <strong>⚠️ {name}</strong><br/>
                {critical_count} critical / {len(s.get('alerts', []))} total alerts • Risk: {risk_label}<br/>
                <small>Rule engine assessment</small>
            </div>
            """, unsafe_allow_html=True)

            col_a, col_b, col_c = st.columns([1, 1, 2])
            with col_a:
                if st.button("View", key=f"risk_view_{s['student_id']}_{idx}"):
                    navigate_to("student-detail", s['student_id'])
            with col_b:
                # create a compiled message to notify
                subject = f"Risk alerts for {name} ({risk_label})"
                compiled = "\n".join([f"- [{a.get('severity').upper()}] {a.get('type')}: {a.get('message')}" for a in s.get('alerts', [])])
                if st.button("Notify Student", key=f"risk_notify_{s['student_id']}_{idx}"):
                    add_alert(s['student_id'], subject, compiled, advisor='Advisor')
                    to_email = f"{s['student_id'].lower()}@example.edu"
                    sent, info = send_email(to_email, subject, compiled)
                    if sent:
                        st.success(f"Email sent to {to_email}")
                    else:
                        st.warning(f"Email not sent: {info}")
            with col_c:
                st.write("")
    else:
        st.info("✅ No active risk alerts")

    st.divider()

    # Student Cards
    st.markdown("### Student List")
    
    if len(filtered_df) == 0:
        st.warning("No students found matching your criteria.")
    else:
        for idx, row in filtered_df.iterrows():
            # use synthesized attributes
            risk_level = row.get('risk_label', 'Medium')
            attendance = _safe_int(row.get('attendance_pct'), 0)
            unpaid = _safe_float(row.get('unpaid_fees'), 0.0)
            financial_aid = row.get('financial_aid_status', 'On time')
            engagement = _safe_int(row.get('engagement_score'), 50)
            gpa_drop = _safe_float(row.get('gpa_drop'), 0.0)
            study_hours = _safe_int(row.get('study_hours'), 0)
            warnings = _safe_int(row.get('warnings_count'), 0)
            risk_score = _safe_int(row.get('risk_score'), 0)
            gpa_value = _safe_float(row.get('gpa'), None)
            gpa_display = f"{gpa_value:.2f}" if gpa_value is not None else "N/A"
            credits_val = _safe_int(row.get('credits'), 0)

            # Risk badge colors
            if risk_level == "High":
                badge_style = '<span class="risk-badge high">🔴 High Risk</span>'
            elif risk_level == "Medium":
                badge_style = '<span class="risk-badge medium">🟡 Medium Risk</span>'
            else:
                badge_style = '<span class="risk-badge low">🟢 Low Risk</span>'

            # Financial status color
            fin_color = "#EF4444" if unpaid > 500 else "#10B981"
            
            col1, col2, col3, col4, col5 = st.columns([1, 2, 1.5, 1.5, 1])

            with col1:
                display_name = row['name'] if 'name' in row.index and pd.notna(row['name']) else str(row.get('student_id', 'Student'))
                initials = "".join([part[0] for part in str(display_name).split()[:2]]) or "S"
                st.markdown(f"<div style='font-size: 24px; text-align: center;'>{initials}</div>", unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div>
                    <strong>{row.get('name', row.get('student_id', 'Student'))}</strong><br/>
                    <small>{row.get('student_id', '')} • {row.get('major', '')}</small><br/>
                    <small>{row.get('year', '')}</small>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(badge_style, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div style='font-size: 12px; line-height: 1.5;'>
                    <strong>GPA:</strong> {gpa_display}<br/>
                    <strong>Attendance:</strong> {attendance}%<br/>
                    <strong>Unpaid Fees:</strong> <span style='color: {fin_color}; font-weight: bold;'>${unpaid:.0f}</span><br/>
                    <strong>Engagement:</strong> {engagement}
                </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown(f"""
                <div style='font-size: 12px; line-height: 1.5;'>
                    <strong>Risk Score:</strong> {risk_score}<br/>
                    <strong>Credits:</strong> {credits_val}<br/>
                    <strong>Warnings:</strong> {warnings}
                </div>
                """, unsafe_allow_html=True)

            with col5:
                if st.button("View", key=f"view_{row['student_id']}", use_container_width=True):
                    navigate_to("student-detail", row['student_id'])

            st.divider()

    nav_left, nav_center, nav_right = st.columns([1, 2, 1])
    with nav_left:
        if st.button("⬅️ Previous", disabled=current_page <= 1):
            st.session_state.advisor_page = max(1, current_page - 1)
            st.rerun()
    with nav_center:
        st.markdown(f"<div style='text-align:center; padding-top:10px;'>Page {current_page} of {total_pages}</div>", unsafe_allow_html=True)
    with nav_right:
        if st.button("Next ➡️", disabled=current_page >= total_pages):
            st.session_state.advisor_page = min(total_pages, current_page + 1)
            st.rerun()
