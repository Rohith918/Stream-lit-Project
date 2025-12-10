import math
import textwrap
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
        .report-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 18px;
            align-items: stretch;
        }
        .report-card {
            border-radius: 14px;
            padding: 18px;
            border: 1px solid #E5E7EB;
            background: linear-gradient(135deg, rgba(0,40,85,0.02), rgba(245,183,0,0.05));
            box-shadow: 0 10px 25px rgba(15, 23, 42, 0.12);
            min-height: 190px;
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        .report-card::after {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: 14px;
            border: 1px solid rgba(255, 255, 255, 0.4);
            pointer-events: none;
        }
        .report-card h4 {
            margin: 0;
            color: #0F172A;
            font-size: 1.05rem;
            font-weight: 700;
        }
        .report-id {
            font-size: 12px;
            color: #6B7280;
            margin-top: 4px;
        }
        .report-chip {
            display: inline-flex;
            align-items: center;
            padding: 4px 12px;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 12px;
            margin-top: 10px;
        }
        .chip-high { background: #FEE2E2; color: #991B1B; }
        .chip-medium { background: #FEF3C7; color: #92400E; }
        .chip-low { background: #DCFCE7; color: #065F46; }
        .report-summary {
            font-size: 13px;
            color: #1F2937;
            margin-top: 12px;
            line-height: 1.5;
            flex: 1;
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

        color_map = {
            "High": "chip-high",
            "Medium": "chip-medium",
            "Low": "chip-low"
        }
        cards = []
        for row in page_records:
            chip_class = color_map.get(row.get("Risk", "Low"), "chip-low")
            display_name = row.get("Name") or row.get("Student ID", "Student")
            summary_html = textwrap.dedent(f"""
            <div class="report-card">
                <h4>{display_name}</h4>
                <div class="report-id">{row.get('Student ID', '')}</div>
                <div class="report-chip {chip_class}">{row.get('Risk', 'Low')} Risk</div>
                <div class="report-summary">{row.get('Summary', 'No summary')}</div>
            </div>
            """).strip()
            cards.append(summary_html)

        st.markdown(f"<div class='report-grid'>{''.join(cards)}</div>", unsafe_allow_html=True)

    st.markdown("### Detailed Table")
    st.dataframe(rep.drop(columns=['Name'], errors='ignore'), use_container_width=True, hide_index=True)

    csv = rep.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, file_name="risk_report.csv", mime="text/csv")
