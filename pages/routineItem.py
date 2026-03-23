from __future__ import annotations

from datetime import date

import streamlit as st

from core.entities import new_uuid
from core.layout import bootstrap_page
from core.routine_service import (
    CADENCE_OPTIONS,
    TASK_STATE_PENDING,
    empty_routine_draft,
    routine_draft_from_existing,
    save_routine_draft,
)

bootstrap_page("Routine Details")

routines = st.session_state.data.setdefault("routines", {})
routine_id = st.session_state.get("routine_view_id")
is_editing_existing = bool(routine_id and routine_id in routines)
source_id = routine_id if is_editing_existing else None

current_source = st.session_state.get("routine_draft_source_id")
if not isinstance(st.session_state.get("routine_draft"), dict) or current_source != source_id:
    if is_editing_existing:
        st.session_state.routine_draft = routine_draft_from_existing(routines[routine_id])
    else:
        st.session_state.routine_draft = empty_routine_draft()
    st.session_state.routine_draft_source_id = source_id

routine = st.session_state.routine_draft
editor_id = routine.get("id") or new_uuid()
routine["id"] = editor_id

st.title("🔁 Routine Details")
st.caption("Edit the selected routine and save changes.")

if st.button("Back to Routines"):
    st.session_state.routine_draft = None
    st.session_state.routine_draft_source_id = None
    st.switch_page("pages/routines.py")

routine["title"] = st.text_input("Title", value=routine.get("title", ""), key=f"routine_title_{editor_id}")

current_cadence = routine.get("cadence", "Daily")
if current_cadence not in CADENCE_OPTIONS:
    current_cadence = "Daily"
cadence = st.selectbox(
    "Cadence",
    CADENCE_OPTIONS,
    index=CADENCE_OPTIONS.index(current_cadence),
    key=f"routine_cadence_{editor_id}",
)
routine["cadence"] = cadence

routine["start_time"] = st.text_input(
    "Start Time (HH:MM)",
    value=routine.get("start_time", "09:00"),
    key=f"routine_start_{editor_id}",
)

if cadence == "Weekly":
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    current = routine.get("day_of_week") if routine.get("day_of_week") is not None else 0
    routine["day_of_week"] = st.selectbox(
        "Day of Week",
        options=list(range(7)),
        index=int(current),
        format_func=lambda x: day_names[x],
        key=f"routine_dow_{editor_id}",
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
        key=f"routine_dom_{editor_id}",
    )
    routine["day_of_week"] = None
    routine["anchor_date"] = None
elif cadence in {"3-Month", "6-Month", "Yearly"}:
    default_anchor = date.fromisoformat(routine["anchor_date"]) if routine.get("anchor_date") else date.today()
    routine["anchor_date"] = st.date_input("Anchor Date", value=default_anchor, key=f"routine_anchor_{editor_id}").isoformat()
    routine["day_of_week"] = None
    routine["day_of_month"] = None
else:
    routine["day_of_week"] = None
    routine["day_of_month"] = None
    routine["anchor_date"] = None

st.markdown("#### Subtasks")
for idx, task in enumerate(routine.get("tasks", [])):
    task.setdefault("id", new_uuid())
    task.setdefault("state", TASK_STATE_PENDING)
    task.setdefault("postpone_until", None)
    c1, c2 = st.columns([8, 1])
    task["title"] = c1.text_input(
        "Task",
        value=task.get("title", ""),
        key=f"routine_task_{editor_id}_{task['id']}",
        label_visibility="collapsed",
        placeholder=f"Task {idx + 1}",
    )
    if c2.button("✕", key=f"routine_task_del_{editor_id}_{task['id']}"):
        routine["tasks"] = [t for t in routine.get("tasks", []) if t.get("id") != task.get("id")]
        st.rerun()

if st.button("Add Subtask", key=f"routine_add_task_{editor_id}"):
    routine.setdefault("tasks", []).append({"id": new_uuid(), "title": "", "state": TASK_STATE_PENDING, "postpone_until": None})
    st.rerun()

save_col, del_col = st.columns([1, 1])
if save_col.button("Save Routine", type="primary"):
    save_result = save_routine_draft(
        routines,
        routine,
        existing_routine_id=source_id,
        today=date.today(),
    )
    if not save_result.ok:
        for err in save_result.errors or []:
            st.error(err)
    else:
        st.session_state.routine_view_id = save_result.routine_id
        st.session_state.routine_draft = None
        st.session_state.routine_draft_source_id = None
        st.switch_page("pages/routines.py")

if del_col.button("Delete Routine"):
    if source_id:
        routines.pop(source_id, None)
    st.session_state.routine_view_id = None
    st.session_state.routine_draft = None
    st.session_state.routine_draft_source_id = None
    st.switch_page("pages/routines.py")
