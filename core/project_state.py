from __future__ import annotations

from copy import deepcopy
from datetime import date

import streamlit as st

from core.entities import parse_date_only
from core.page_state import clear_selection_keys, flags_store, ui_store

PROJECT_EDITOR_NS = "project_editor"
DRAFT_PROJECT_NS = "draft_project"

PROJECT_DEFAULTS = {
    "title": "",
    "description": "",
    "due_date": None,
    "status": "Active",
}


def empty_draft() -> dict:
    return {
        "title": "",
        "description": "",
        "due_date": None,
        "status": "Active",
        "draft_actions": [],
        "draft_delegations": [],
    }


def draft_linked_count(draft: dict) -> int:
    return len(draft.get("draft_actions", [])) + len(draft.get("draft_delegations", []))


def get_draft_project_ui() -> dict:
    editor = ui_store().get(DRAFT_PROJECT_NS)
    if not isinstance(editor, dict):
        source = st.session_state.get("draft_project") or empty_draft()
        editor = deepcopy(source)
        editor.setdefault("draft_actions", [])
        editor.setdefault("draft_delegations", [])
        ui_store()[DRAFT_PROJECT_NS] = editor
        st.session_state.draft_project = deepcopy(editor)
    return editor


def sync_draft_runtime(draft: dict) -> None:
    st.session_state.draft_project = deepcopy(draft)


def clear_draft_runtime() -> None:
    ui_store().pop(DRAFT_PROJECT_NS, None)
    ui_store().pop("draft_action_editor", None)
    ui_store().pop("draft_delegation_editor", None)
    flags_store().pop("reset::draft_action_editor", None)
    flags_store().pop("reset::draft_delegation_editor", None)
    st.session_state.draft_project = None


def append_draft_action(draft: dict, item: dict) -> None:
    draft.setdefault("draft_actions", []).append(item)


def append_draft_delegation(draft: dict, item: dict) -> None:
    draft.setdefault("draft_delegations", []).append(item)


def remove_draft_linked_item(*, draft: dict, item: dict) -> str:
    if item.get("kind") == "delegation":
        draft["draft_delegations"] = [row for row in draft.get("draft_delegations", []) if row is not item]
        sync_draft_runtime(draft)
        return "Draft delegation removed."

    draft["draft_actions"] = [row for row in draft.get("draft_actions", []) if row is not item]
    sync_draft_runtime(draft)
    return "Draft action removed."


def clear_linked_item_modal_state() -> None:
    flags_store().pop("project_linked_item_modal", None)
    flags_store().pop("project_linked_item_modal_editor_key", None)


def load_project_editor(project: dict) -> dict:
    editor = ui_store().get(PROJECT_EDITOR_NS)
    if not isinstance(editor, dict):
        editor = deepcopy(PROJECT_DEFAULTS)
        ui_store()[PROJECT_EDITOR_NS] = editor

    snapshot = (
        project.get("title", ""),
        project.get("description", ""),
        project.get("due_date"),
        project.get("status", "Active"),
    )
    if (
        editor.get("loaded_project_id") != project.get("id")
        or editor.get("source_snapshot") != snapshot
        or bool(flags_store().pop("reload_project_editor", False))
    ):
        editor.update(
            {
                "title": project.get("title", ""),
                "description": project.get("description", ""),
                "due_date": parse_date_only(project.get("due_date")),
                "status": project.get("status", "Active"),
                "loaded_project_id": project.get("id"),
                "source_snapshot": snapshot,
            }
        )
        clear_linked_item_modal_state()
        clear_selection_keys("project_linked_items::")
        flags_store()["suppress_linked_item_selection_once"] = True
        flags_store()[f"reset::{PROJECT_EDITOR_NS}"] = True
    return editor


def editor_text(editor: dict, field: str) -> str:
    return str(editor.get(field, "") or "").strip()


def editor_date_value(editor: dict, field: str) -> str | None:
    raw_value = editor.get(field)
    if raw_value in (None, ""):
        return None
    if isinstance(raw_value, date):
        return raw_value.isoformat()
    parsed = parse_date_only(raw_value)
    return parsed.isoformat() if parsed else None


def set_delete_mode(project_id: str | None) -> None:
    flags_store()["project_delete_mode"] = project_id
    st.session_state.project_delete_mode = project_id


def get_delete_mode() -> str | None:
    flags = flags_store()
    if "project_delete_mode" not in flags:
        flags["project_delete_mode"] = st.session_state.get("project_delete_mode")
    return flags.get("project_delete_mode")
