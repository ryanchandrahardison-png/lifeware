
import streamlit as st
from core.state import init_state
from core.layout import sidebar_file_controls

st.set_page_config(page_title="Lifeware Control Engine", layout="wide")

init_state()

data = st.session_state.data

st.sidebar.title("Lifeware")

sidebar_file_controls(data)

st.sidebar.markdown("---")

st.sidebar.page_link("pages/home.py", label="Home", icon="🏠")
st.sidebar.page_link("pages/calendarList.py", label="Calendar", icon="📅")
st.sidebar.page_link("pages/actions.py", label="Actions", icon="✅")
st.sidebar.page_link("pages/delegations.py", label="Delegations", icon="🤝")
st.sidebar.page_link("pages/routines.py", label="Routines", icon="🔁")

st.title("Lifeware Control Engine")
st.write("Use the menu on the left to navigate.")
