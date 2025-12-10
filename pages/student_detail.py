import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from pages._alerts_lib import _ensure_alerts_state, get_alerts_for_student, acknowledge_alert
from pages.advisor_dashboard import load_data, _prepare_student_dataset


def _safe_float(value, default=None):
    """Return a float or the provided default without raising."""
    if isinstance(value, pd.Series):
        value = value.iloc[0] if len(value) > 0 else None
    if value is None or pd.isna(value):
        return default
    try:
        converted = float(value)
        return converted if not pd.isna(converted) else default
    except (TypeError, ValueError):
        return default


def _safe_int(value, default=0):
    """Return an int or default without raising."""
    num = _safe_float(value, None)
    if num is None:
        return default
    try:
        return int(num)
    except (TypeError, ValueError):
        return default

def get_student_data(student_id, df):
    """Get specific student data"""
    if 'student_id' not in df.columns:
        return None
    student = df[df['student_id'] == student_id]
    if len(student) > 0:
        return student.iloc[0]
    return None

def risk_level_from_gpa(gpa):
    """Determine risk level from GPA.
    Requirement: GPA < 2.0 is At Risk (High)."""
    try:
        if gpa is None or pd.isna(gpa):
            return "Medium"
        g = float(gpa)
    except Exception:
        return "Medium"
    if g < 2.0:
        return "High"
    elif g < 3.0:
        return "Medium"
    return "Low"

def render(student_id, navigate_to):
    """Render Student Detail View"""
    _ensure_alerts_state()

    # Load data
    df = _prepare_student_dataset(load_data())
    student = get_student_data(student_id, df)

    if student is None:
        st.error(f"❌ Student {student_id} not found")
        if st.button("⬅️ Back to Advisor Dashboard"):
            navigate_to("advisor")
        return

    st.markdown("""
    <div class="header-container">
        <div class="header-title">👤 Student Profile</div>
        <div class="header-subtitle">Detailed academic and engagement performance</div>
    </div>
    """, unsafe_allow_html=True)

    # Navigation Bar
    if st.button("⬅️ Back to Advisor Dashboard", use_container_width=True):
        navigate_to("advisor")

    st.divider()

    # Show any in-app notifications for this student
    notes = get_alerts_for_student(student_id)
    if notes:
        st.markdown("### 🔔 Notifications")
        for i, n in enumerate(notes):
            st.warning(f"**{n['subject']}** — {n['date']}\n\n{n['message']}")
            ack_key = f"ack_note_{student_id}_{i}"
            if st.button("Acknowledge", key=ack_key):
                ok = acknowledge_alert(student_id, i)
                if ok:
                    st.rerun()
                else:
                    st.error("Could not acknowledge notification")

    # Student Header Info
    col1, col2, col3, col4, col5, col6 = st.columns([0.5, 2, 1.5, 1.5, 1.5, 1.5])

    gpa_val = _safe_float(student.get('gpa', None) if isinstance(student, pd.Series) else None, None)
    risk_level = risk_level_from_gpa(gpa_val)
    if risk_level == "High":
        badge_html = '<span class="risk-badge high">🔴 High Risk</span>'
    elif risk_level == "Medium":
        badge_html = '<span class="risk-badge medium">🟡 Medium Risk</span>'
    else:
        badge_html = '<span class="risk-badge low">🟢 Low Risk</span>'

    with col1:
        display_name = student.get('name', student.get('student_id', 'Student')) if isinstance(student, pd.Series) else 'Student'
        initials = "".join([p[0] for p in str(display_name).split()[:2]]) or "S"
        st.markdown(f"<div style='font-size: 32px; text-align: center;'>{initials}</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div>
            <h3 style='margin: 0; color: #002855;'>{student.get('name', student.get('student_id', 'Student'))}</h3>
            <p style='margin: 5px 0; font-size: 13px; color: #666;'>{student.get('student_id', '')} • {student.get('major', '')}</p>
            <p style='margin: 5px 0; font-size: 13px; color: #666;'>{student.get('year', '')}</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(badge_html, unsafe_allow_html=True)

    with col3:
        gpa_display = f"{gpa_val:.2f}" if gpa_val is not None else "N/A"
        st.metric("GPA", gpa_display)

    with col4:
        st.metric("Credits", _safe_int(student.get('credits', 0)))

    with col5:
        st.metric("Year", student.get('year', ''))

    with col6:
        major_val = str(student.get('major', ''))
        st.metric("Major", major_val[:10])

    st.divider()

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📚 Academic Performance",
        "📋 Attendance & Engagement",
        "💰 Financial Overview",
        "🔧 Intervention History"
    ])

    # =========================================================================
    # TAB 1: ACADEMIC PERFORMANCE
    # =========================================================================
    with tab1:
        col1, col2, col3 = st.columns(3)

        # Safe GPA access
        safe_gpa = gpa_val
        gpa_text = f"{safe_gpa:.2f}" if safe_gpa is not None else "N/A"

        with col1:
            st.metric("Current GPA", gpa_text)

        with col2:
            st.metric("Credits Completed", _safe_int(student.get('credits', 0)))

        with col3:
            if safe_gpa is not None:
                academic_status = "Good Standing" if float(safe_gpa) >= 2.5 else "Academic Warning"
            else:
                academic_status = "Unknown"
            st.metric("Academic Status", academic_status)

        st.markdown("---")

        # Mock GPA trend
        st.markdown("### 📈 GPA Trend Over Time")
        gpa_trend = pd.DataFrame({
            'Semester': ['Fall 22', 'Spring 23', 'Fall 23', 'Spring 24', 'Fall 24', 'Spring 25'],
            'GPA': [2.8, 2.7, 2.5, 2.3, 2.1, 2.1]
        })

        fig_gpa = px.line(
            gpa_trend,
            x='Semester',
            y='GPA',
            markers=True,
            line_shape='linear',
            color_discrete_sequence=['#002855'],
            height=300
        )
        fig_gpa.add_hline(y=2.0, line_dash="dash", line_color="red", annotation_text="Academic Warning Line", annotation_position="right")
        fig_gpa.add_hline(y=2.5, line_dash="dash", line_color="orange", annotation_text="At-Risk Line", annotation_position="right")
        fig_gpa.update_layout(
            hovermode='x unified',
            margin=dict(l=0, r=0, t=30, b=0),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Arial, sans-serif", color="#002855")
        )
        fig_gpa.update_traces(marker=dict(size=8, color='#F5B700'))
        st.plotly_chart(fig_gpa, use_container_width=True)

        # Current courses
        st.markdown("### 📖 Current Courses (Spring 2025)")
        courses_df = pd.DataFrame({
            'Course': ['MATH 301', 'CS 401', 'ENG 201', 'PHYS 350'],
            'Grade': ['B-', 'C+', 'A-', 'B'],
            'Credits': [3, 4, 3, 3],
            'Status': ['In Progress', 'In Progress', 'In Progress', 'In Progress']
        })
        st.dataframe(courses_df, use_container_width=True, hide_index=True)

    # =========================================================================
    # TAB 2: ATTENDANCE & ENGAGEMENT
    # =========================================================================
    with tab2:
        col1, col2, col3 = st.columns(3)

        with col1:
            base_gpa = safe_gpa if safe_gpa is not None else 2.5
            attendance_pct = min(100, max(50, int(75 + (base_gpa - 2.5) * 10)))
            st.metric("Attendance Rate", f"{attendance_pct}%")

        with col2:
            base_gpa2 = safe_gpa if safe_gpa is not None else 2.5
            engagement_score = min(100, max(20, int(60 + (base_gpa2 - 2.0) * 15)))
            st.metric("Engagement Score", engagement_score)

        with col3:
            st.metric("Late Submissions", "2")

        st.markdown("---")

        # Mock attendance by course
        st.markdown("### 📊 Attendance by Course")
        attendance_df = pd.DataFrame({
            'Course': ['MATH 301', 'CS 401', 'ENG 201', 'PHYS 350'],
            'Attendance %': [75, 68, 92, 78]
        })

        fig_att = px.bar(
            attendance_df,
            x='Course',
            y='Attendance %',
            color='Attendance %',
            color_continuous_scale=['#EF4444', '#F59E0B', '#10B981'],
            height=300
        )
        fig_att.update_layout(
            hovermode='x unified',
            margin=dict(l=0, r=0, t=30, b=0),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Arial, sans-serif", color="#002855")
        )
        st.plotly_chart(fig_att, use_container_width=True)

        # Engagement activities
        st.markdown("### 🎯 Recent Engagement")
        engagement_items = [
            ("Study Group Participation", "Feb 10, 2025", "✓"),
            ("Office Hours Visit", "Feb 8, 2025", "✓"),
            ("Tutoring Session", "Feb 5, 2025", "✓"),
            ("Library Lab Usage", "Daily Average", "Active"),
        ]
        for activity, date, status in engagement_items:
            st.markdown(f"• **{activity}** — {date} ({status})")

    # =========================================================================
    # TAB 3: FINANCIAL OVERVIEW
    # =========================================================================
    with tab3:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Outstanding Balance", "$0")

        with col2:
            st.metric("Aid Status", "Current")

        with col3:
            st.metric("Enrollment Status", "Full-Time")

        st.markdown("---")

        # Payment history
        st.markdown("### 💳 Payment History")
        payment_df = pd.DataFrame({
            'Date': ['2025-01-15', '2024-12-10', '2024-11-05'],
            'Description': ['Spring 2025 Tuition', 'Fall 2024 Balance', 'Fall 2024 Tuition'],
            'Amount': ['$5,000.00', '$2,500.00', '$5,000.00'],
            'Status': ['Paid', 'Paid', 'Paid']
        })
        st.dataframe(payment_df, use_container_width=True, hide_index=True)

        # Funding sources
        st.markdown("### 📋 Funding Sources")
        funding_df = pd.DataFrame({
            'Type': ['Federal Loan', 'Institutional Grant', 'State Grant'],
            'Amount': ['$4,000', '$1,500', '$2,000'],
            'Status': ['Active', 'Active', 'Active']
        })
        st.dataframe(funding_df, use_container_width=True, hide_index=True)

    # =========================================================================
    # TAB 4: INTERVENTION HISTORY
    # =========================================================================
    with tab4:
        st.markdown("### 📝 Intervention Record")

        # Display existing interventions
        if student_id in st.session_state['interventions']:
            for intervention in st.session_state['interventions'][student_id]:
                st.info(f"**{intervention['type']}** (by {intervention['advisor']}) - {intervention['date']}\n\n{intervention['notes']}")
        else:
            st.write("No interventions recorded yet.")

        st.markdown("---")

        # Add new intervention form
        st.markdown("### ➕ Create New Intervention")

        with st.form(f"intervention_form_{student_id}"):
            col1, col2 = st.columns(2)

            with col1:
                int_type = st.selectbox(
                    "Intervention Type",
                    ["Academic Support", "Financial Aid", "Attendance Outreach", "Mental Health Referral", "Career Counseling", "Other"],
                    key=f"int_type_{student_id}"
                )

            with col2:
                advisor_name = st.text_input("Advisor Name", key=f"advisor_{student_id}")

            notes = st.text_area("Notes", placeholder="Describe the intervention and recommended actions...", key=f"notes_{student_id}")

            submitted = st.form_submit_button("✅ Save Intervention", use_container_width=True)

            if submitted:
                if advisor_name.strip() == "":
                    st.error("Please enter advisor name")
                else:
                    if student_id not in st.session_state['interventions']:
                        st.session_state['interventions'][student_id] = []

                    intervention = {
                        'type': int_type,
                        'advisor': advisor_name,
                        'notes': notes,
                        'date': datetime.now().strftime("%Y-%m-%d %H:%M")
                    }

                    st.session_state['interventions'][student_id].append(intervention)
                    st.success(f"✅ Intervention recorded for {student['student_id'] if isinstance(student, pd.Series) else student_id}")
                    st.rerun()

    st.divider()

    # Back button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("⬅️ Back to Advisor Dashboard", use_container_width=True, key="back_button_detail"):
            navigate_to("advisor")
