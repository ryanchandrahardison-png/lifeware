from __future__ import annotations

from copy import deepcopy

import streamlit as st


def ui_store() -> dict:
    st.session_state.setdefault("ui", {})
    return st.session_state.ui


def flags_store() -> dict:
    st.session_state.setdefault("flags", {})
    return st.session_state.flags


def widget_key(namespace: str, field: str) -> str:
    return f"{namespace}__{field}"


def pop_reset_flag(namespace: str) -> bool:
    return bool(flags_store().pop(f"reset::{namespace}", False))


def prepare_widget_defaults(namespace: str, fields: list[str], editor: dict, *, force: bool = False) -> None:
    for field in fields:
        key = widget_key(namespace, field)
        if force or key not in st.session_state:
            st.session_state[key] = editor.get(field)


def sync_editor_from_widgets(namespace: str, fields: list[str], editor: dict) -> None:
    for field in fields:
        editor[field] = st.session_state.get(widget_key(namespace, field))


def reset_editor_namespace(namespace: str, defaults: dict) -> None:
    ui_store()[namespace] = deepcopy(defaults)
    flags_store()[f"reset::{namespace}"] = True


def clear_selection_keys(prefix: str) -> None:
    keys_to_clear = [key for key in st.session_state.keys() if str(key).startswith(prefix)]
    for key in keys_to_clear:
        st.session_state.pop(key, None)


def reset_project_detail_runtime_state() -> None:
    st.session_state.project_delete_mode = None
    ui = ui_store()
    for key in ["project_editor", "draft_project", "draft_action_editor", "draft_delegation_editor"]:
        ui.pop(key, None)

    flags = flags_store()
    for key in [
        "project_delete_mode",
        "project_linked_item_modal",
        "project_linked_item_modal_editor_key",
        "suppress_linked_item_selection_once",
        "reload_project_editor",
        "reset::project_editor",
        "reset::draft_action_editor",
        "reset::draft_delegation_editor",
    ]:
        flags.pop(key, None)

    clear_selection_keys("project_linked_items::")


def reset_state_for_uploaded_file() -> None:
    st.session_state.event_view_id = None
    st.session_state.event_new_mode = False
    st.session_state.action_view_id = None
    st.session_state.delegation_view_id = None
    st.session_state.routine_view_id = None
    st.session_state.project_view_id = None
    st.session_state.project_delete_mode = None
    st.session_state.draft_project = None
    st.session_state.return_to_project_on_back = False
    st.session_state.return_project_view_id = None
    reset_project_detail_runtime_state()
