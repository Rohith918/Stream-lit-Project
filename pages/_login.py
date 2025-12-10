import streamlit as st
from pathlib import Path

_USERS = {
    "advisor1": "password123",
    "admin": "adminpass",
}


def render(navigate_to):
    st.markdown(
        """
        <style>
          :root {
            --hsu-primary: #2563EB;
            --hsu-muted: #64748B;
          }
          .login-title-text {
            text-align: center;
            color: var(--hsu-primary);
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 4px;
          }
          .login-subtitle-text {
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 0.4px;
            font-size: 12px;
            color: var(--hsu-muted);
            margin-bottom: 18px;
          }
          .login-footer {
            color: #94A3B8;
            font-size: 12px;
            text-align: center;
            margin-top: 16px;
          }
          .login-error {
            color: #DC2626;
            font-size: 13px;
            text-align: center;
            margin-bottom: 10px;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "login_error" not in st.session_state:
        st.session_state.login_error = None

    logo_path = Path("templates/img/logo.png")
    center = st.columns([1, 2, 1])[1]
    with center:
        if logo_path.exists():
            st.image(str(logo_path), use_column_width=True)
        st.markdown("<div class='login-title-text'>Horizon State University</div>", unsafe_allow_html=True)
        st.markdown("<div class='login-subtitle-text'>Advisor Portal</div>", unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Sign in", use_container_width=True)

        if submitted:
            if username in _USERS and _USERS[username] == password:
                st.session_state.login_error = None
                st.session_state["authenticated"] = True
                st.session_state["user"] = username
                navigate_to("institutional")
                st.stop()
            else:
                st.session_state.login_error = "Invalid credentials. Please try again."

        if st.session_state.login_error:
            st.markdown(f"<div class='login-error'>{st.session_state.login_error}</div>", unsafe_allow_html=True)

        st.markdown("<div class='login-footer'>Need help? Contact IT support.</div>", unsafe_allow_html=True)
