from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any

import streamlit as st


DEFAULT_STATUS_OPTIONS = ["Not Started", "In Progress", "Waiting", "Complete"]
DATE_FIELD_CANDIDATES = ["due_date", "due", "when", "date"]
FOLLOW_UP_FIELD_CANDIDATES = ["follow_up_date", "follow_up", "due_date", "due", "when", "date"]
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
        if "T" in text:
            text = text.split("T", 1)[0]
        return date.fromisoformat(text)
    except Exception:
        return None


def _status_index(status: str) -> int:
    if status in DEFAULT_STATUS_OPTIONS:
        return DEFAULT_STATUS_OPTIONS.index(status)
    return 0


def _delete_known_date_keys(record: dict, field_candidates: list[str]) -> None:
    for key in field_candidates:
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
    date_label: str = "Due Date",
    date_field_candidates: list[str] | None = None,
) -> None:
    items = data.setdefault(list_key, [])
    is_edit = index is not None and 0 <= index < len(items)
    date_field_candidates = date_field_candidates or DATE_FIELD_CANDIDATES

    original = _as_dict(items[index]) if is_edit else {}

    default_title = _pick(original, title_keys, "")
    default_details = _pick(original, ["details", "description", "notes"], "")
    default_status = _pick(original, ["status", "state"], DEFAULT_STATUS_OPTIONS[0])
    default_due_date = _parse_iso_date(_pick(original, date_field_candidates, "")) if show_due_date else None

    st.title(f"{title_emoji} {page_title}")
    st.caption(subtitle_text if is_edit else f"Create a new {page_title.lower()}.")

    with st.form(f"{list_key}_detail_form"):
        title = st.text_input("Title", value=default_title)

        due_date_value = None
        if show_due_date:
            due_date_kwargs = {"value": default_due_date if default_due_date is not None else date.today()}
            if not is_edit:
                due_date_kwargs["min_value"] = date.today()
            due_date_value = st.date_input(date_label, **due_date_kwargs)

        details = st.text_area("Details", value=default_details, height=180)

        status = st.selectbox(
            "Status",
            DEFAULT_STATUS_OPTIONS,
            index=_status_index(default_status),
        )

        action_cols = st.columns(3)
        save = action_cols[0].form_submit_button("Save Changes" if is_edit else "Create")
        delete = action_cols[1].form_submit_button("Delete", disabled=not is_edit)
        back = action_cols[2].form_submit_button("Back")

    index_key = f"{list_key[:-1]}_view_index"

    if back:
        st.session_state[index_key] = None
        st.switch_page(back_page)
        return

    if delete and is_edit:
        del items[index]
        st.session_state[index_key] = None
        st.switch_page(back_page)
        return

    if save:
        clean_title = title.strip()
        if not clean_title:
            st.error("Title is required.")
            return

        updated = deepcopy(original) if is_edit else {}
        updated = _sanitize_source_keys(updated)
        updated[title_keys[0]] = clean_title

        if show_due_date and due_date_value is not None:
            _delete_known_date_keys(updated, date_field_candidates)
            updated[date_field_candidates[0]] = due_date_value.isoformat()

        if details.strip():
            updated["details"] = details.strip()
        else:
            updated.pop("details", None)
            updated.pop("description", None)
            updated.pop("notes", None)

        if status:
            updated["status"] = status
            updated.pop("state", None)

        if is_edit:
            items[index] = updated
        else:
            items.append(updated)

        st.session_state[index_key] = None
        st.switch_page(back_page)
