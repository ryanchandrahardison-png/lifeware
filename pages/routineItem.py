from __future__ import annotations

from datetime import date

import streamlit as st

from core.entities import new_uuid
from core.layout import sidebar_file_controls
from core.navigation import render_primary_navigation
from core.routine_service import CADENCE_OPTIONS, ensure_routine_shape, reset_due_instance_if_needed, validate_routine_payload
from core.state import init_state

st.set_page_config(page_title="Routine Details", layout="wide")
init_state()
sidebar_file_controls()

render_primary_navigation()

routines = st.session_state.data.setdefault("routines", {})
routine_id = st.session_state.get("routine_view_id")

if routine_id and routine_id in routines:
    routine = routines[routine_id]
else:
    routine = {
        "id": new_uuid(),
        "title": "",
        "cadence": "Daily",
        "start_time": "09:00",
        "day_of_week": None,
        "day_of_month": None,
        "anchor_date": None,
        "tasks": [{"id": new_uuid(), "title": "", "state": "pending", "postpone_until": None}],
        "active_instance_key": None,
    }
    routine_id = routine["id"]
    routines[routine_id] = routine
    st.session_state.routine_view_id = routine_id

ensure_routine_shape(routine)

st.title("🔁 Routine Details")
st.caption("Edit the selected routine and save changes.")

if st.button("Back to Routines"):
    st.switch_page("pages/routines.py")

routine["title"] = st.text_input("Title", value=routine.get("title", ""), key=f"routine_title_{routine_id}")

cadence = st.selectbox(
    "Cadence",
    CADENCE_OPTIONS,
    index=CADENCE_OPTIONS.index(routine.get("cadence", "Daily")),
    key=f"routine_cadence_{routine_id}",
)
routine["cadence"] = cadence

routine["start_time"] = st.text_input(
    "Start Time (HH:MM)",
    value=routine.get("start_time", "09:00"),
    key=f"routine_start_{routine_id}",
)

if cadence == "Weekly":
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    current = routine.get("day_of_week") if routine.get("day_of_week") is not None else 0
    routine["day_of_week"] = st.selectbox(
        "Day of Week",
        options=list(range(7)),
        index=int(current),
        format_func=lambda x: day_names[x],
        key=f"routine_dow_{routine_id}",
    )
    routine["day_of_month"] = None
    routine["anchor_date"] = None
elif cadence == "Monthly":
    routine["day_of_month"] = st.number_input(
        "Day of Month",
        min_value=1,
        max_value=31,
        value=int(routine.get("day_of_month") or 1),
        step=1,
        key=f"routine_dom_{routine_id}",
    )
    routine["day_of_week"] = None
    routine["anchor_date"] = None
elif cadence in {"3-Month", "6-Month", "Yearly"}:
    default_anchor = date.fromisoformat(routine["anchor_date"]) if routine.get("anchor_date") else date.today()
    routine["anchor_date"] = st.date_input("Anchor Date", value=default_anchor, key=f"routine_anchor_{routine_id}").isoformat()
    routine["day_of_week"] = None
    routine["day_of_month"] = None
else:
    routine["day_of_week"] = None
    routine["day_of_month"] = None
    routine["anchor_date"] = None

st.markdown("#### Subtasks")
for idx, task in enumerate(routine.get("tasks", [])):
    c1, c2 = st.columns([8, 1])
    task["title"] = c1.text_input(
        "Task",
        value=task.get("title", ""),
        key=f"routine_task_{routine_id}_{task['id']}",
        label_visibility="collapsed",
        placeholder=f"Task {idx + 1}",
    )
    if c2.button("✕", key=f"routine_task_del_{routine_id}_{task['id']}"):
        routine["tasks"] = [t for t in routine.get("tasks", []) if t.get("id") != task.get("id")]
        st.rerun()

if st.button("Add Subtask", key=f"routine_add_task_{routine_id}"):
    routine.setdefault("tasks", []).append({"id": new_uuid(), "title": "", "state": "pending", "postpone_until": None})
    st.rerun()

save_col, del_col = st.columns([1, 1])
if save_col.button("Save Routine", type="primary"):
    result = validate_routine_payload(routine)
    if not result.ok:
        for err in result.errors or []:
            st.error(err)
    else:
        if routine.get("day_of_month") is not None:
            routine["day_of_month"] = int(routine["day_of_month"])
        reset_due_instance_if_needed(routine, today=date.today())
        st.switch_page("pages/routines.py")

if del_col.button("Delete Routine"):
    routines.pop(routine_id, None)
    st.session_state.routine_view_id = None
    st.switch_page("pages/routines.py")
