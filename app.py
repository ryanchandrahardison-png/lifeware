import streamlit as st
from core.state import init_session_state

st.set_page_config(page_title="Lifeware Control Engine", layout="wide")
init_session_state()

home = st.Page("pages/home.py", title="Home", icon="🏠", default=True)
calendar_list = st.Page("pages/calendarList.py", title="Calendar", icon="📅")
calendar_event = st.Page("pages/calendarEvent.py", title="Calendar Event", icon="📝")
actions = st.Page("pages/actions.py", title="Actions", icon="✅")
delegations = st.Page("pages/delegations.py", title="Delegations", icon="🤝")
routines = st.Page("pages/routines.py", title="Routines", icon="🔁")

pg = st.navigation(
    {
        "Main": [home],
        "Planning": [calendar_list, calendar_event],
        "Execution": [actions, delegations, routines],
    }
)
pg.run()
