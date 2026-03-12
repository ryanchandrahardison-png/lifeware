from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import streamlit as st

from core.calendar_utils import parse_dt_any
from core.entities import is_completed_status, is_waiting_status, parse_date_only
from core.layout import sidebar_file_controls
from core.routine_service import apply_postpone, reset_due_instance_if_needed, routine_due_today
from core.state import init_state

st.set_page_config(page_title="My Day", layout="wide")
init_state()
sidebar_file_controls()

st.sidebar.markdown("---")
st.sidebar.page_link("app.py", label="Home", icon="🏠")
st.sidebar.page_link("pages/calendarList.py", label="Calendar", icon="📅")
st.sidebar.page_link("pages/actions.py", label="Actions", icon="✅")
st.sidebar.page_link("pages/delegations.py", label="Delegations", icon="🤝")
st.sidebar.page_link("pages/projects.py", label="Projects", icon="📁")
st.sidebar.page_link("pages/routines.py", label="Routines", icon="🔁")
st.sidebar.page_link("pages/myDay.py", label="My Day", icon="☀️")

st.title("☀️ My Day")
st.caption("Today view across calendar, actions, delegations, and routines.")

now = datetime.now()
today = date.today()
data = st.session_state.data

# Calendar due today
calendar_rows: list[dict] = []
for event in data.get("events", {}).values():
    start = parse_dt_any(event.get("start_utc") or event.get("start"))
    if start and start.date() == today:
        calendar_rows.append(
            {
                "Title": event.get("title") or "Untitled",
                "Start": start.strftime("%H:%M"),
                "Status": event.get("status", ""),
            }
        )

st.subheader("Calendar Today")
if calendar_rows:
    st.dataframe(pd.DataFrame(sorted(calendar_rows, key=lambda r: r["Start"])), use_container_width=True, hide_index=True)
else:
    st.caption("No calendar events today.")

# Actions due today
action_rows: list[dict] = []
for action in data.get("actions", {}).values():
    due = parse_date_only(action.get("due_date"))
    if due == today and not is_completed_status(action.get("status")):
        action_rows.append({"Title": action.get("title") or "Untitled", "Status": action.get("status", "")})

st.subheader("Actions Due Today")
if action_rows:
    st.dataframe(pd.DataFrame(action_rows), use_container_width=True, hide_index=True)
else:
    st.caption("No actions due today.")

# Delegations due today
del_rows: list[dict] = []
for delegation in data.get("delegations", {}).values():
    follow_up = parse_date_only(delegation.get("follow_up_date"))
    if follow_up == today and not is_completed_status(delegation.get("status")):
        del_rows.append({"Title": delegation.get("title") or "Untitled", "Status": delegation.get("status", "")})

st.subheader("Delegations Due Today")
if del_rows:
    st.dataframe(pd.DataFrame(del_rows), use_container_width=True, hide_index=True)
else:
    st.caption("No delegations due today.")

# Routines due today
st.subheader("Routines Due Today")
routines = data.get("routines", {})
due_routines = [routine for routine in routines.values() if routine_due_today(routine, today=today)]

def _postpone_defaults(task_id: str) -> tuple[int, int, int]:
    return (
        int(st.session_state.get(f"postpone_days_{task_id}", 0)),
        int(st.session_state.get(f"postpone_hours_{task_id}", 0)),
        int(st.session_state.get(f"postpone_minutes_{task_id}", 0)),
    )

if not due_routines:
    st.caption("No routines due today.")
else:
    for routine in sorted(due_routines, key=lambda r: (r.get("start_time", ""), r.get("title", ""))):
        reset_due_instance_if_needed(routine, today=today)
        done = sum(1 for task in routine.get("tasks", []) if task.get("state") == "completed")
        total = len(routine.get("tasks", []))
        with st.expander(f"{routine.get('start_time', '--:--')} · {routine.get('title', 'Untitled')} ({done}/{total})", expanded=True):
            for task in routine.get("tasks", []):
                row = st.columns([4, 1, 1, 2])
                state = task.get("state", "pending")
                label = task.get("title") or "Untitled task"
                postpone_until = task.get("postpone_until")
                suffix = f" · postponed to {postpone_until}" if state == "postponed" and postpone_until else ""
                row[0].markdown(f"**{label}**  \\n`{state}`{suffix}")
                if row[1].button("Yes", key=f"routine_yes_{routine['id']}_{task['id']}"):
                    task["state"] = "completed"
                    task["postpone_until"] = None
                    st.rerun()
                if row[2].button("No", key=f"routine_no_{routine['id']}_{task['id']}"):
                    task["state"] = "pending"
                    task["postpone_until"] = None
                    st.rerun()

                days, hours, minutes = _postpone_defaults(task["id"])
                c1, c2, c3, c4 = row[3].columns([1, 1, 1, 1])
                d = c1.number_input("D", min_value=0, max_value=31, value=days, key=f"postpone_days_{task['id']}")
                h = c2.number_input("H", min_value=0, max_value=23, value=hours, key=f"postpone_hours_{task['id']}")
                m = c3.number_input("M", min_value=0, max_value=59, value=minutes, key=f"postpone_minutes_{task['id']}")
                if c4.button("Postpone", key=f"routine_postpone_{routine['id']}_{task['id']}"):
                    result = apply_postpone(task, routine, days=int(d), hours=int(h), minutes=int(m), now=now)
                    if not result.ok:
                        for err in result.errors or []:
                            st.error(err)
                    else:
                        st.rerun()
