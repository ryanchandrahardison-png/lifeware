import streamlit as st
from core.state import init_state
from core.layout import sidebar_file_controls
from core.navigation import render_primary_navigation

st.set_page_config(page_title="Lifeware Control Engine", layout="wide")

init_state()
sidebar_file_controls()

render_primary_navigation()

st.title("Lifeware Control Engine")
st.write("Use the menu on the left to navigate.")
