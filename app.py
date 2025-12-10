import streamlit as st
import sys

# Verify running through streamlit
if "streamlit.runtime.scriptrunner" not in sys.modules:
    st.error("❌ Please run with: streamlit run app.py")
    st.stop()

# ============================================================================
# PAGE CONFIG & THEME
# ============================================================================
st.set_page_config(
    page_title="Student Success Intelligence",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS Theme - Light palette
st.markdown("""
<style>
    :root {
        --primary: #2563EB;
        --primary-light: #E0EAFF;
        --accent: #F97316;
        --surface: #F8FAFC;
        --card: #FFFFFF;
        --border: #E2E8F0;
        --text: #0F172A;
        --muted: #64748B;
    }

    body, .main {
        background-color: var(--surface);
        color: var(--text);
    }

    .header-container {
        background: linear-gradient(135deg, #EEF2FF 0%, #DBEAFE 100%);
        padding: 20px 30px;
        margin: -60px -30px 30px -30px;
        border-bottom: 1px solid var(--border);
    }

    .header-title {
        color: var(--text);
        font-size: 28px;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .header-subtitle {
        color: var(--muted);
        font-size: 12px;
        margin-top: 5px;
    }

    .nav-button {
        background-color: var(--card);
        color: var(--text);
        border: 1px solid var(--border);
        padding: 10px 20px;
        border-radius: 10px;
        cursor: pointer;
        font-weight: 600;
        font-size: 14px;
        transition: all 0.3s ease;
        margin-right: 10px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
    }

    .nav-button:hover,
    .nav-button.active {
        background-color: var(--primary);
        color: #fff;
        border-color: var(--primary);
    }

    .kpi-card {
        background: var(--card);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid var(--border);
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
        margin-bottom: 20px;
    }

    .kpi-label {
        font-size: 12px;
        color: var(--muted);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .kpi-value {
        font-size: 32px;
        font-weight: 700;
        color: var(--text);
        margin: 8px 0;
    }

    .kpi-subtext {
        font-size: 12px;
        color: var(--muted);
    }

    .risk-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }

    .risk-badge.high { background-color: #FEE2E2; color: #B91C1C; }
    .risk-badge.medium { background-color: #FEF3C7; color: #B45309; }
    .risk-badge.low { background-color: #DCFCE7; color: #15803D; }

    button {
        background-color: var(--primary) !important;
        color: #fff !important;
        border: none !important;
        font-weight: 600 !important;
    }

    button:hover {
        background-color: #1D4ED8 !important;
    }

    .stTabs [data-baseweb="tab-list"] button {
        background-color: transparent;
        color: var(--muted);
        border: none;
        border-bottom: 2px solid transparent;
        padding: 10px 20px;
        font-weight: 500;
    }

    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: var(--primary);
        border-bottom-color: var(--primary);
        font-weight: 700;
    }

    .alert-box {
        background-color: #FFF7ED;
        border-left: 4px solid var(--accent);
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 10px;
    }

    .student-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        transition: box-shadow 0.3s ease;
    }

    .student-card:hover {
        box-shadow: 0 10px 18px rgba(15, 23, 42, 0.08);
    }

    .chart-container {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }

    .chart-title {
        font-size: 14px;
        font-weight: 700;
        color: var(--text);
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 2px solid #E5E7EB;
    }

    .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: var(--text);
    }

    .metric-label {
        font-size: 12px;
        color: var(--muted);
        font-weight: 600;
    }

    .alert-box, .student-card { word-wrap: break-word; overflow-wrap: anywhere; }
    .alert-box small { display: inline-block; margin-top: 6px; opacity: 0.85; }

    .stButton > button { min-height: 38px !important; padding: 10px 14px !important; border-radius: 10px !important; }
    .stButton { margin: 4px 0; }

    .stDataFrame, .stTable { overflow-x: auto; background: var(--card); border-radius: 12px; }

    @media (max-width: 900px) {
        .header-container {
            padding: 16px;
            margin: -40px -16px 20px -16px;
        }

        .header-title { font-size: 22px; }
        .nav-button { padding: 8px 12px; font-size: 13px; }
        .kpi-card { padding: 16px; }
        .chart-container { padding: 16px; }
        .student-card { padding: 12px; }
        .stTabs [data-baseweb="tab-list"] button { padding: 8px 12px; }
    }

    @media (max-width: 600px) {
        .header-title { font-size: 18px; }
        .header-subtitle { font-size: 11px; }
        .nav-button { padding: 6px 10px; font-size: 12px; }
        .student-card { padding: 10px; }
        .alert-box { padding: 10px; }
        .stTabs [data-baseweb="tab-list"] button { padding: 6px 8px; font-size: 12px; }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
if "current_screen" not in st.session_state:
    st.session_state.current_screen = "institutional"

if "selected_student_id" not in st.session_state:
    st.session_state.selected_student_id = None

if "search_query" not in st.session_state:
    st.session_state.search_query = ""

if "risk_filter" not in st.session_state:
    st.session_state.risk_filter = "All Levels"

if "interventions" not in st.session_state:
    st.session_state.interventions = {}

# Authentication state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user = None

# ============================================================================
# NAVIGATION FUNCTIONS
# ============================================================================
def navigate_to(screen, student_id=None):
    """Navigate to a different screen"""
    st.session_state.current_screen = screen
    if student_id:
        st.session_state.selected_student_id = student_id
    # force a rerun so the new page renders immediately
    try:
        st.rerun()
    except Exception:
        pass

# ============================================================================
# IMPORT PAGE MODULES
# ============================================================================
from pages import institutional_dashboard, advisor_dashboard, student_detail
from pages import alerts_page, reports
from pages import _login as login, _profile as profile

# ============================================================================
# MAIN APP ROUTING
# ============================================================================
def main():
    # If not authenticated, show login first
    if not st.session_state.get('authenticated', False):
        login.render(navigate_to)
        return

    # Render appropriate page based on session state
    if st.session_state.current_screen == "institutional":
        institutional_dashboard.render(navigate_to)
    elif st.session_state.current_screen == "advisor":
        advisor_dashboard.render(navigate_to)
    elif st.session_state.current_screen == "student-detail":
        student_detail.render(st.session_state.selected_student_id, navigate_to)
    elif st.session_state.current_screen == "alerts":
        alerts_page.render(navigate_to)
    elif st.session_state.current_screen == "profile":
        profile.render(navigate_to)
    elif st.session_state.current_screen == "reports":
        reports.render(navigate_to)

if __name__ == "__main__":
    main()
