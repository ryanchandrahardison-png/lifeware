from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any

import streamlit as st


DEFAULT_STATUS_OPTIONS = ["Not Started", "In Progress", "Waiting", "Complete"]
DATE_FIELD_CANDIDATES = ["due_date", "due", "when", "date"]
SOURCE_FIELD_NAMES = {"source"}


def _as_dict(item: Any) -> dict:
    return deepcopy(item) if isinstance(item, dict) else {"title": "" if item is None else str(item)}


def _pick(record: dict, keys: list[str], default: str = "") -> str:
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return str(value)
    return default


def _parse_iso_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    try:
        text = str(value).strip()
        if 'T' in text:
            text = text.split('T', 1)[0]
        return date.fromisoformat(text)
    except Exception:
        return None


def _status_index(status: str) -> int:
    if status in DEFAULT_STATUS_OPTIONS:
        return DEFAULT_STATUS_OPTIONS.index(status)
    return 0


def _delete_known_due_keys(record: dict) -> None:
    for key in DATE_FIELD_CANDIDATES:
        record.pop(key, None)


def _sanitize_source_keys(record: dict) -> dict:
    return {k: v for k, v in record.items() if k not in SOURCE_FIELD_NAMES}


def render_item_detail_form(
    *,
    data: dict,
    list_key: str,
    index: int | None,
    title_emoji: str,
    page_title: str,
    back_page: str,
    back_label: str,
    title_keys: list[str],
    subtitle_text: str,
    show_due_date: bool = False,
) -> None:
    items = data.setdefault(list_key, [])
    is_edit = index is not None and 0 <= index < len(items)

    if not is_edit:
        st.info(f"No {page_title.lower()} is selected.")
        if st.button(back_label):
            st.session_state[f"{list_key[:-1]}_view_index"] = None
            st.switch_page(back_page)
        return

    original = _as_dict(items[index])

    default_title = _pick(original, title_keys, "")
    default_details = _pick(original, ["details", "description", "notes"], "")
    default_status = _pick(original, ["status", "state"], DEFAULT_STATUS_OPTIONS[0])
    default_due_date = _parse_iso_date(_pick(original, DATE_FIELD_CANDIDATES, "")) if show_due_date else None
    if show_due_date and default_due_date is None:
        default_due_date = date.today()

    st.title(f"{title_emoji} {page_title}")
    st.caption(subtitle_text)

    with st.form(f"{list_key}_detail_form"):
        title = st.text_input("Title", value=default_title)

        due_date_value = None
        if show_due_date:
            due_date_kwargs = {"value": default_due_date}
            if not is_edit:
                due_date_kwargs["min_value"] = date.today()
            due_date_value = st.date_input("Due Date", **due_date_kwargs)

        details = st.text_area("Details", value=default_details, height=180)

        status = st.selectbox(
            "Status",
            DEFAULT_STATUS_OPTIONS,
            index=_status_index(default_status),
        )

        action_cols = st.columns(3)
        save = action_cols[0].form_submit_button("Save Changes")
        delete = action_cols[1].form_submit_button("Delete")
        back = action_cols[2].form_submit_button("Back")

    index_key = f"{list_key[:-1]}_view_index"

    if back:
        st.session_state[index_key] = None
        st.switch_page(back_page)
        return

    if delete:
        del items[index]
        st.session_state[index_key] = None
        st.switch_page(back_page)
        return

    if save:
        clean_title = title.strip()
        if not clean_title:
            st.error("Title is required.")
            return

        updated = deepcopy(original)
        updated = _sanitize_source_keys(updated)
        updated[title_keys[0]] = clean_title

        if show_due_date and due_date_value is not None:
            _delete_known_due_keys(updated)
            updated["due_date"] = due_date_value.isoformat()

        if details.strip():
            updated["details"] = details.strip()
        else:
            updated.pop("details", None)

        if status:
            updated["status"] = status
            updated.pop("state", None)

        items[index] = updated
        st.session_state[index_key] = None
        st.switch_page(back_page)
