import streamlit as st
from core.state import init_state
from core.layout import sidebar_file_controls

st.set_page_config(page_title="Lifeware", layout="wide")
init_state()
data = st.session_state.data
st.sidebar.title("Navigation")
sidebar_file_controls(data)
st.title("Lifeware Control Engine")
st.write("Use the navigation menu to manage your system.")