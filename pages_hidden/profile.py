import streamlit as st
import pandas as pd
from pages import student_detail
from pages.advisor_dashboard import load_data


def render(navigate_to):
    st.markdown("""
    <div class='header-container'>
        <div class='header-title'>👤 Profile</div>
        <div class='header-subtitle'>View a student profile</div>
    </div>
    """, unsafe_allow_html=True)

    df = load_data()
    if 'student_id' not in df.columns:
        st.error("Student data is missing required identifiers.")
        return

    id_series = df['student_id'].astype(str)
    if 'name' in df.columns:
        name_series = df['name'].fillna("").astype(str)
        name_series = name_series.str.strip()
        name_series = name_series.where(name_series != "", id_series)
    else:
        name_series = id_series

    display_options = [f"{sid} - {name}" for sid, name in zip(id_series, name_series)]
    mapping = dict(zip(display_options, id_series))

    if not mapping:
        st.info("No students available to display.")
        return

    choice = st.selectbox("Select student to view profile", options=["Choose..."] + display_options)
    if choice and choice != "Choose...":
        sid = mapping[choice]
        navigate_to('student-detail', sid)

    st.markdown("---")
    st.markdown("<small>Select a student to open their detailed profile.</small>", unsafe_allow_html=True)
