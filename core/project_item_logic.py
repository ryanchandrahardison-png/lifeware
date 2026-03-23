from __future__ import annotations

from core.project_state import editor_date_value, editor_text


def build_draft_action_payload(editor: dict) -> dict:
    return {
        "title": editor_text(editor, "title"),
        "details": editor_text(editor, "details"),
        "due_date": editor_date_value(editor, "date"),
        "status": "Open",
        "is_active_global": bool(editor.get("active_global", False)),
    }


def build_draft_delegation_payload(editor: dict) -> dict:
    return {
        "title": editor_text(editor, "title"),
        "details": editor_text(editor, "details"),
        "follow_up_date": editor_date_value(editor, "date"),
        "status": "Waiting",
        "is_active_global": bool(editor.get("active_global", False)),
    }


def build_project_action_payload(editor: dict) -> dict:
    return {
        "title": editor_text(editor, "title"),
        "details": editor_text(editor, "details"),
        "due_date": editor_date_value(editor, "date"),
        "is_active_global": bool(editor.get("active_global", False)),
    }


def build_project_delegation_payload(editor: dict) -> dict:
    return {
        "title": editor_text(editor, "title"),
        "details": editor_text(editor, "details"),
        "follow_up_date": editor_date_value(editor, "date"),
        "is_active_global": bool(editor.get("active_global", False)),
    }
