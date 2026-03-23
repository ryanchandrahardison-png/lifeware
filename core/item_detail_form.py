from __future__ import annotations

from datetime import date

import streamlit as st

from core.item_detail_logic import (
    build_item_defaults,
    build_item_snapshot,
    delete_item_with_project_guard,
    detail_index_key,
    item_editor_config,
    restore_project_return_context,
    save_item_with_constraints,
    status_index,
)
from core.page_state import (
    flags_store,
    pop_reset_flag,
    prepare_widget_defaults,
    sync_editor_from_widgets,
    ui_store,
    widget_key,
)


def _init_editor_state(*, namespace: str, item_id: str | None, defaults: dict, status_options: list[str], is_edit: bool) -> dict:
    editor = ui_store().get(namespace)
    snapshot = build_item_snapshot(item_id=item_id, defaults=defaults, is_edit=is_edit)
    if not isinstance(editor, dict):
        editor = {}
        ui_store()[namespace] = editor

    if editor.get("source_snapshot") != snapshot:
        editor.update(
            {
                "title": defaults["title"],
                "details": defaults["details"],
                "status": defaults["status"] if defaults["status"] in status_options else status_options[0],
                "due_date": defaults["due_date"] if defaults["due_date"] is not None else date.today(),
                "source_snapshot": snapshot,
            }
        )
        flags_store()[f"reset::{namespace}"] = True
    return editor


def _render_form_actions(*, is_edit: bool, back_label: str) -> tuple[bool, bool, bool]:
    action_cols = st.columns(3)
    save = action_cols[0].form_submit_button("Save Changes" if is_edit else "Create")
    delete = action_cols[1].form_submit_button("Delete", disabled=not is_edit)
    back = action_cols[2].form_submit_button(back_label)
    return save, delete, back


def _cleanup_and_navigate(*, list_key: str, namespace: str, back_page: str) -> None:
    st.session_state[detail_index_key(list_key)] = None
    ui_store().pop(namespace, None)
    flags_store().pop(f"reset::{namespace}", None)
    restore_project_return_context(session_state=st.session_state, back_page=back_page)
    st.switch_page(back_page)


def render_item_detail_form(
    *,
    data: dict,
    list_key: str,
    item_id: str | None,
    title_emoji: str,
    page_title: str,
    back_page: str,
    back_label: str,
    title_keys: list[str],
    subtitle_text: str,
    show_due_date: bool = False,
    date_label: str | None = None,
    date_field_candidates: list[str] | None = None,
    status_options: list[str] | None = None,
) -> None:
    items = data.setdefault(list_key, {})
    is_edit = item_id is not None and item_id in items
    editor_config = item_editor_config(list_key)
    date_field_candidates = date_field_candidates or editor_config["date_field_candidates"]
    status_options = status_options or editor_config["status_options"]
    date_label = date_label or editor_config["date_label"]

    original = items.get(item_id, {}) if is_edit else {}
    defaults = build_item_defaults(
        original=original,
        title_keys=title_keys,
        status_options=status_options,
        show_due_date=show_due_date,
        date_field_candidates=date_field_candidates,
    )

    namespace = f"{list_key}_detail_editor"
    editor = _init_editor_state(
        namespace=namespace,
        item_id=item_id,
        defaults=defaults,
        status_options=status_options,
        is_edit=is_edit,
    )

    fields = ["title", "details", "status"] + (["due_date"] if show_due_date else [])
    prepare_widget_defaults(namespace, fields, editor, force=pop_reset_flag(namespace))

    st.title(f"{title_emoji} {page_title}")
    st.caption(subtitle_text if is_edit else f"Create a new {page_title.lower()}.")

    with st.form(f"{list_key}_detail_form"):
        st.text_input("Title", key=widget_key(namespace, "title"))

        if show_due_date:
            due_date_kwargs = {"key": widget_key(namespace, "due_date")}
            if not is_edit:
                due_date_kwargs["min_value"] = date.today()
            st.date_input(date_label, **due_date_kwargs)

        st.text_area("Details", key=widget_key(namespace, "details"), height=180)

        st.selectbox(
            "Status",
            status_options,
            index=status_index(str(editor.get("status", status_options[0])), status_options),
            key=widget_key(namespace, "status"),
        )

        sync_editor_from_widgets(namespace, fields, editor)
        save, delete, back = _render_form_actions(is_edit=is_edit, back_label=back_label)

    if back:
        _cleanup_and_navigate(list_key=list_key, namespace=namespace, back_page=back_page)
        return

    if delete and is_edit:
        ok, errors = delete_item_with_project_guard(data=data, list_key=list_key, item_id=item_id)
        if not ok:
            for error in errors:
                st.error(error)
            return
        _cleanup_and_navigate(list_key=list_key, namespace=namespace, back_page=back_page)
        return

    if save:
        due_date_value = editor.get("due_date") if show_due_date else None
        ok, errors, _updated = save_item_with_constraints(
            data=data,
            list_key=list_key,
            item_id=item_id,
            title=str(editor.get("title", "") or ""),
            details=str(editor.get("details", "") or ""),
            status=str(editor.get("status", status_options[0]) or status_options[0]),
            date_value=due_date_value,
            date_field_candidates=date_field_candidates,
        )
        if not ok:
            for error in errors:
                st.error(error)
            return

        _cleanup_and_navigate(list_key=list_key, namespace=namespace, back_page=back_page)
