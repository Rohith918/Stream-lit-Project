import math
import streamlit as st
import pandas as pd
from pages.advisor_dashboard import load_data, synthesize_student_profile, compute_weighted_risk


def _brief_summary(row: pd.Series) -> str:
    parts = []
    gpa = row.get('gpa', None)
    if pd.notna(gpa):
        try:
            g = float(gpa)
            if g < 2.0:
                parts.append('Low GPA')
            elif g < 2.5:
                parts.append('At-risk GPA')
        except Exception:
            pass
    if float(row.get('unpaid_fees', 0) or 0) > 500:
        parts.append('Unpaid fees')
    if int(row.get('attendance_pct', 100) or 100) < 80:
        parts.append('Low attendance')
    if int(row.get('warnings_count', 0) or 0) >= 2:
        parts.append('Multiple warnings')
    if int(row.get('counseling_visits', 0) or 0) < 1 or int(row.get('engagement_score', 100) or 100) < 50:
        parts.append('Low engagement')
    if not parts:
        parts.append('No major risks')
    return ', '.join(parts[:3])


def render(navigate_to):
    st.markdown("""
    <div class="header-container">
        <div class="header-title">📑 Reports</div>
        <div class="header-subtitle">Brief risk summaries per student</div>
    </div>
    """, unsafe_allow_html=True)

    # Back to Home
    if st.button("⬅️ Back to Home", use_container_width=True):
        navigate_to('institutional')

    st.markdown("""
    <style>
        .report-card {
            border-radius: 8px;
            padding: 16px;
            border: 1px solid #E5E7EB;
            background: #FFFFFF;
            box-shadow: 0 6px 15px rgba(0, 40, 85, 0.08);
            min-height: 120px;
        }
        .report-card h4 {
            margin: 0;
            color: #111827;
            font-size: 1rem;
        }
        .report-chip {
            display: inline-flex;
            align-items: center;
            padding: 2px 10px;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 12px;
            margin-top: 6px;
        }
        .report-chip.high { background: #FEE2E2; color: #B91C1C; }
        .report-chip.medium { background: #FEF3C7; color: #B45309; }
        .report-chip.low { background: #DCFCE7; color: #15803D; }
        .report-summary {
            font-size: 13px;
            color: #4B5563;
            margin-top: 10px;
            line-height: 1.4;
        }
    </style>
    """, unsafe_allow_html=True)

    df = load_data()
    search_col, risk_col, _, _ = st.columns([2, 1, 1, 1])
    with search_col:
        search_query = st.text_input("Search by student ID or name", key="reports_search")
    with risk_col:
        risk_filter = st.selectbox("Risk filter", ["All", "High", "Medium", "Low"], key="reports_risk_filter")

    # Synthesize minimal attributes and risk
    out_rows = []
    for _, r in df.iterrows():
        prof = synthesize_student_profile(r)
        score, label = compute_weighted_risk(prof, r.get('gpa', None))
        brief = _brief_summary({**r.to_dict(), **prof})
        out_rows.append({
            'Student ID': r.get('student_id', ''),
            'Name': r.get('name', ''),
            'Risk': label,
            'Summary': f"{label} risk — {brief}"
        })

    rep = pd.DataFrame(out_rows)

    st.markdown("### Summary")

    records = rep.to_dict("records")
    if search_query:
        q = search_query.strip().lower()
        records = [
            row for row in records
            if q in str(row.get("Student ID", "")).lower()
            or q in str(row.get("Name", "")).lower()
        ]
    if risk_filter != "All":
        records = [row for row in records if row.get("Risk") == risk_filter]
    if not records:
        st.info("No students available to summarize.")
    else:
        if "reports_page_size" not in st.session_state:
            st.session_state.reports_page_size = 6
        if "reports_page" not in st.session_state:
            st.session_state.reports_page = 1

        size_options = [6, 9, 12]
        page_size = st.selectbox("Cards per page", size_options, key="reports_page_size")
        total_pages = max(1, math.ceil(len(records) / page_size))
        if st.session_state.reports_page > total_pages:
            st.session_state.reports_page = total_pages

        nav_left, nav_center, nav_right = st.columns([1, 2, 1])
        with nav_left:
            if st.button("⬅️ Previous", disabled=st.session_state.reports_page <= 1, key="reports_prev"):
                st.session_state.reports_page = max(1, st.session_state.reports_page - 1)
                st.rerun()
        with nav_center:
            st.markdown(f"<div style='text-align:center; padding-top:10px;'>Page {st.session_state.reports_page} of {total_pages}</div>", unsafe_allow_html=True)
        with nav_right:
            if st.button("Next ➡️", disabled=st.session_state.reports_page >= total_pages, key="reports_next"):
                st.session_state.reports_page = min(total_pages, st.session_state.reports_page + 1)
                st.rerun()

        start = (st.session_state.reports_page - 1) * page_size
        end = start + page_size
        page_records = records[start:end]

        cols = st.columns(3)
        color_map = {
            "High": "high",
            "Medium": "medium",
            "Low": "low"
        }
        for idx, row in enumerate(page_records):
            chip_class = color_map.get(row.get("Risk", "Low"), "low")
            summary_html = f"""
            <div class="report-card">
                <h4>{row.get('Student ID', 'Student')}</h4>
                <div class="report-chip {chip_class}">{row.get('Risk', 'Low')} Risk</div>
                <div class="report-summary">{row.get('Summary', 'No summary')}</div>
            </div>
            """
            with cols[idx % 3]:
                st.markdown(summary_html, unsafe_allow_html=True)

    st.markdown("### Detailed Table")
    st.dataframe(rep, use_container_width=True, hide_index=True)

    csv = rep.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, file_name="risk_report.csv", mime="text/csv")
