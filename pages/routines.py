from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from core.entities import new_uuid
from core.layout import sidebar_file_controls
from core.routine_service import (
    CADENCE_OPTIONS,
    ensure_routine_shape,
    reset_due_instance_if_needed,
    routine_due_today,
    validate_routine_payload,
)
from core.selection_utils import selected_single_row_index
from core.state import init_state

st.set_page_config(page_title="Routines", layout="wide")
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

st.title("🔁 Routines")
st.caption("Define cadenced routines here. Execute routine subtasks in My Day.")

for routine in st.session_state.data.get("routines", {}).values():
    ensure_routine_shape(routine)
    reset_due_instance_if_needed(routine, today=date.today())

if "routine_view_id" not in st.session_state:
    st.session_state.routine_view_id = None


def _new_routine() -> dict:
    return {
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


if st.button("New Routine"):
    routine = _new_routine()
    st.session_state.data.setdefault("routines", {})[routine["id"]] = routine
    st.session_state.routine_view_id = routine["id"]
    st.rerun()

routines = st.session_state.data.get("routines", {})

def _render_routine_table() -> None:
    rows = []
    ids = []
    for routine_id, routine in sorted(routines.items(), key=lambda item: (item[1].get("start_time", ""), item[1].get("title", ""))):
        rows.append(
            {
                "Title": routine.get("title") or "Untitled",
                "Cadence": routine.get("cadence"),
                "Start": routine.get("start_time"),
                "Tasks": len(routine.get("tasks", [])),
                "Due Today": "Yes" if routine_due_today(routine) else "",
            }
        )
        ids.append(routine_id)

    if not rows:
        st.info("No routines yet. Create one to get started.")
        return

    selection = st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="routines_table",
    )
    selected_idx, stale = selected_single_row_index(selection, len(ids))
    if stale:
        st.session_state.pop("routines_table", None)
        return
    if selected_idx is not None:
        st.session_state.routine_view_id = ids[selected_idx]


_render_routine_table()

routine_id = st.session_state.get("routine_view_id")
routine = routines.get(routine_id) if routine_id else None

if not routine:
    st.stop()

ensure_routine_shape(routine)

st.markdown("---")
st.subheader("Routine Editor")

routine["title"] = st.text_input("Title", value=routine.get("title", ""), key=f"routine_title_{routine_id}")

cadence = st.selectbox("Cadence", CADENCE_OPTIONS, index=CADENCE_OPTIONS.index(routine.get("cadence", "Daily")), key=f"routine_cadence_{routine_id}")
routine["cadence"] = cadence

routine["start_time"] = st.text_input("Start Time (HH:MM)", value=routine.get("start_time", "09:00"), key=f"routine_start_{routine_id}")

if cadence == "Weekly":
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    current = routine.get("day_of_week") if routine.get("day_of_week") is not None else 0
    routine["day_of_week"] = st.selectbox("Day of Week", options=list(range(7)), index=int(current), format_func=lambda x: day_names[x], key=f"routine_dow_{routine_id}")
    routine["day_of_month"] = None
    routine["anchor_date"] = None
elif cadence == "Monthly":
    routine["day_of_month"] = st.number_input("Day of Month", min_value=1, max_value=31, value=int(routine.get("day_of_month") or 1), step=1, key=f"routine_dom_{routine_id}")
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
    task["title"] = c1.text_input("Task", value=task.get("title", ""), key=f"routine_task_{routine_id}_{task['id']}", label_visibility="collapsed", placeholder=f"Task {idx + 1}")
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
        # normalize day/month numeric inputs
        if routine.get("day_of_month") is not None:
            routine["day_of_month"] = int(routine["day_of_month"])
        reset_due_instance_if_needed(routine, today=date.today())
        st.success("Routine saved.")

if del_col.button("Delete Routine"):
    routines.pop(routine_id, None)
    st.session_state.routine_view_id = None
    st.rerun()
