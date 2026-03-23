from core.project_linked_item_views import (
    LINKED_ITEM_GROUP_ORDER,
    default_compact_view_from_user_agent,
    linked_item_compact_label,
    linked_item_display_rows,
    requires_draft_link_warning,
)


def test_group_order_is_stable_for_project_tables():
    assert LINKED_ITEM_GROUP_ORDER == ("Completed", "Past Due", "Upcoming", "Floating")


def test_default_compact_view_detects_mobile_user_agents():
    assert default_compact_view_from_user_agent("Mozilla iPhone Safari") is True
    assert default_compact_view_from_user_agent("Mozilla/5.0 desktop") is False


def test_linked_item_display_rows_formats_expected_columns():
    rows = linked_item_display_rows([
        {"kind": "action", "title": "Ship", "due_date": "2026-03-25"},
    ])
    assert rows == [{"Task Name": "Ship", "Type": "Action", "Date": "2026-03-25"}]


def test_linked_item_compact_label_combines_title_type_and_date():
    label = linked_item_compact_label({"kind": "delegation", "title": "Follow up", "follow_up_date": "2026-03-28"})
    assert "Follow up" in label
    assert "Delegation" in label
    assert "2026-03-28" in label


def test_requires_draft_link_warning_only_for_unsaved_draft_items():
    assert requires_draft_link_warning(item_id=None, draft={}) is True
    assert requires_draft_link_warning(item_id="id-1", draft={}) is False
    assert requires_draft_link_warning(item_id=None, draft=None) is False
