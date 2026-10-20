"""Unit tests for DynamoDB single-table operations."""

from common.store import (
    get_current_card,
    get_events_for_date,
    get_household_settings,
    mark_card_dismissed,
    put_current_card,
    put_event_history,
    put_event_if_absent,
    put_household_settings,
)


def test_put_event_if_absent_dedupe(mock_dynamodb):
    # First write should succeed
    is_new = put_event_if_absent("req_dedupe_1", {"data": "test"})
    assert is_new is True

    # Immediate second write with same request_id must return False
    is_duplicate = put_event_if_absent("req_dedupe_1", {"data": "test"})
    assert is_duplicate is False


def test_current_card_lifecycle(mock_dynamodb):
    card = {
        "cardId": "req_card_1",
        "accountId": "acct_test",
        "severity": "attention",
        "headline": "Someone is at the door",
        "sentence": "A courier is holding a parcel.",
        "deviceName": "Front Door",
        "timeLocal": "2026-10-18T10:00:00Z",
        "createdAt": "2026-10-18T10:00:00Z",
    }
    put_current_card(card)

    fetched = get_current_card("acct_test")
    assert fetched is not None
    assert fetched["cardId"] == "req_card_1"
    assert fetched["severity"] == "attention"
    assert fetched.get("dismissedAt") is None

    # Dismiss card
    dismissed = mark_card_dismissed("acct_test")
    assert dismissed is True

    updated = get_current_card("acct_test")
    assert updated is not None
    assert updated.get("dismissedAt") is not None


def test_household_settings(mock_dynamodb):
    # Default settings when none stored
    default_settings = get_household_settings("acct_new")
    assert default_settings["timezone"] == "America/Los_Angeles"
    assert default_settings["flashIntensity"] == "high"

    # Custom update
    custom_settings = {
        "accountId": "acct_new",
        "timezone": "America/New_York",
        "deviceNames": {"dev_1": "Porch"},
        "expectedVisitors": [],
        "quietHours": {"start": "23:00", "end": "07:00"},
        "flashIntensity": "low",
    }
    put_household_settings("acct_new", custom_settings)

    saved = get_household_settings("acct_new")
    assert saved["timezone"] == "America/New_York"
    assert saved["flashIntensity"] == "low"


def test_event_history_and_query(mock_dynamodb):
    event = {
        "requestId": "req_hist_1",
        "accountId": "acct_hist",
        "type": "button_press",
        "deviceId": "dev_front",
        "occurredAt": "2026-10-18T14:30:00Z",
    }
    card = {"headline": "Doorbell pressed", "sentence": "Someone is at the door."}
    put_event_history(event, card)

    events = get_events_for_date("acct_hist", "2026-10-18")
    assert len(events) == 1
    assert events[0]["requestId"] == "req_hist_1"
    assert events[0]["card"]["headline"] == "Doorbell pressed"
