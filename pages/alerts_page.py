import math
from typing import Dict, List
import streamlit as st
from pages._alerts_lib import (
    _ensure_alerts_state,
    acknowledge_alert,
    send_email,
    is_email_configured,
)
from utils.alert_logic import AlertSystem
from pages.advisor_dashboard import load_data, _build_alert_dataframe


def _slice(records: List[Dict], size: int, page: int) -> List[Dict]:
    start = (page - 1) * size
    end = start + size
    return records[start:end]


def _render_alert_card(navigate_to, student_id: str, student_name: str, alert: Dict, idx: int, source: str, unique: int):
    subj = alert.get('subject') or alert.get('type', 'Alert')
    severity = alert.get('severity', 'warning')
    color = AlertSystem.get_alert_color(severity)
    message = alert.get('message', '')
    date = alert.get('date', '')

    st.markdown(
        f"""
        <div style="border-left: 6px solid {color}; padding: 10px 14px; background: #fff; border-radius: 10px; margin-bottom: 10px;">
            <div><strong>{student_name}</strong> • {student_id}</div>
            <div style="margin-top:4px;"><strong>{subj}</strong> — <small>{date or "Generated now"}</small></div>
            <div style="margin-top:6px;">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("View Student", key=f"{source}_view_{student_id}_{idx}_{unique}"):
            navigate_to('student-detail', student_id)
    with col2:
        if source == "state":
            if st.button("Acknowledge", key=f"{source}_ack_{student_id}_{idx}_{unique}"):
                ok = acknowledge_alert(student_id, idx)
                if ok:
                    st.rerun()
                else:
                    st.error("Failed to acknowledge")
    with col3:
        mailto_body = message.replace("\n", "%0A")
        mailto_link = f"mailto:{student_id.lower()}@example.edu?subject={subj}&body={mailto_body}"
        st.markdown(
            f"""
            <a href="{mailto_link}" target="_blank" style="text-decoration:none;">
                <div style="background-color:#2563EB;color:#fff;padding:8px 12px;border-radius:6px;text-align:center;">
                    Resend Email
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )


def _filter_records(records: List[Dict], search_query: str, severity_filter: str) -> List[Dict]:
    filtered = records
    if search_query:
        q = search_query.lower()
        filtered = [r for r in filtered if q in (r['student_id'] or '').lower() or q in (r['alert'].get('subject', '').lower())]
    if severity_filter != "All":
        filtered = [r for r in filtered if r['alert'].get('severity', '').capitalize() == severity_filter]
    return filtered


def _flatten_state_alerts(notifications: Dict[str, List[Dict]], name_lookup: Dict[str, str]) -> List[Dict]:
    flat = []
    for student_id, notes in notifications.items():
        for idx, note in enumerate(notes):
            inferred_sev = 'critical' if 'CRITICAL' in (note.get('subject') or '').upper() else 'warning'
            flat.append({
                'student_id': student_id,
                'student_name': name_lookup.get(student_id, student_id),
                'alert': {
                    'subject': note.get('subject'),
                    'message': note.get('message'),
                    'date': note.get('date', ''),
                    'severity': inferred_sev,
                },
                'idx': idx,
            })
    return flat


def _flatten_live_alerts(name_lookup: Dict[str, str]) -> List[Dict]:
    try:
        df = load_data().copy()
        df_alerts = _build_alert_dataframe(df)
        students_with_alerts, _ = AlertSystem.get_students_with_alerts(df_alerts)
    except Exception:
        return []

    flat = []
    for student in students_with_alerts:
        for alert in student.get('alerts', []):
            sid = student.get('student_id')
            flat.append({
                'student_id': sid,
                'student_name': name_lookup.get(sid, sid),
                'alert': {
                    'subject': alert.get('type'),
                    'message': alert.get('message'),
                    'date': '',
                    'severity': alert.get('severity', 'warning'),
                },
                'idx': 0,
            })
    return flat


def render(navigate_to):
    st.markdown("""
    <div class='header-container'>
        <div class='header-title'>🔔 Alerts</div>
        <div class='header-subtitle'>In-app alerts for students</div>
    </div>
    """, unsafe_allow_html=True)

    _ensure_alerts_state()

    col_nav, col_spacer = st.columns([1, 3])
    with col_nav:
        if st.button("⬅️ Back to Home", use_container_width=True, key="alerts_back_home"):
            navigate_to("institutional")

    search_col, filter_col, size_col = st.columns([2, 1, 1])
    with search_col:
        search_query = st.text_input("Search by student or subject", key="alerts_search")
    with filter_col:
        severity_filter = st.selectbox("Severity", ["All", "Critical", "Warning"], key="alerts_severity")
    with size_col:
        page_size = st.selectbox("Alerts per page", [5, 10, 20], index=1, key="alerts_page_size")

    if "alerts_page" not in st.session_state:
        st.session_state.alerts_page = 1

    notifications = st.session_state.get('notifications', {})
    has_notifications = any(notes for notes in notifications.values())
    base_df = load_data()
    name_lookup = {row['student_id']: row.get('name', row['student_id']) for _, row in base_df.iterrows() if 'student_id' in row}

    if not is_email_configured():
        st.info("Email sending is disabled because SMTP credentials are not configured. Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, and EMAIL_FROM environment variables to enable notifications.")

    records = _flatten_state_alerts(notifications, name_lookup) if has_notifications else _flatten_live_alerts(name_lookup)
    filtered_records = _filter_records(records, search_query, severity_filter)

    total_pages = max(1, math.ceil(len(filtered_records) / page_size))
    st.session_state.alerts_page = min(st.session_state.alerts_page, total_pages)
    current_page = st.session_state.alerts_page

    page_records = _slice(filtered_records, page_size, current_page)

    if not page_records:
        if has_notifications:
            st.info("No alerts match your filters.")
        else:
            st.warning("No live alerts match your filters.")
    else:
        for unique_idx, record in enumerate(page_records):
            source = "state" if has_notifications else "live"
            _render_alert_card(
                navigate_to,
                record['student_id'],
                record.get('student_name', record['student_id']),
                record['alert'],
                record['idx'],
                source,
                unique_idx + (current_page - 1) * page_size,
            )

    nav_left, nav_center, nav_right = st.columns([1, 2, 1])
    with nav_left:
        if st.button("⬅️ Previous", disabled=current_page <= 1):
            st.session_state.alerts_page = max(1, current_page - 1)
            st.rerun()
    with nav_center:
        st.markdown(f"<div style='text-align:center; padding-top:10px;'>Page {current_page} of {total_pages}</div>", unsafe_allow_html=True)
    with nav_right:
        if st.button("Next ➡️", disabled=current_page >= total_pages):
            st.session_state.alerts_page = min(total_pages, current_page + 1)
            st.rerun()
