"""Unit tests for Card creation and severity rules."""

from common.cards import build_card
from common.matcher import MatchResult


def test_card_expected_visitor_calm():
    event = {
        "requestId": "req_c1",
        "accountId": "acct_1",
        "type": "button_press",
        "deviceName": "Front Door",
        "timeLocal": "2026-10-20T10:04:00Z",
    }
    desc = {"sentence": "A nurse is standing at the door.", "visitors": [{"role": "service_worker"}]}
    match = MatchResult(status="expected", matched_id="v1", matched_label="Nurse Priya")

    card = build_card(event, desc, match)
    assert card["severity"] == "calm"
    assert card["headline"] == "Expected visitor"
    assert card["expectedLine"] == "Expected: Nurse Priya"


def test_card_unexpected_button_press_attention():
    event = {
        "requestId": "req_c2",
        "accountId": "acct_1",
        "type": "button_press",
        "deviceName": "Front Door",
        "timeLocal": "2026-10-20T14:30:00Z",
    }
    desc = {"sentence": "Two solicitors with clipboards are at the door.", "visitors": [{"role": "solicitor"}]}
    match = MatchResult(status="unexpected")

    card = build_card(event, desc, match)
    assert card["severity"] == "attention"
    assert card["headline"] == "Someone is at the door"
    assert card["expectedLine"] is None


def test_card_motion_no_visitors_info():
    event = {
        "requestId": "req_c3",
        "accountId": "acct_1",
        "type": "motion_detected",
        "deviceName": "Driveway",
        "timeLocal": "2026-10-20T16:00:00Z",
    }
    desc = {"sentence": "A car is parked in the driveway.", "visitors": []}
    match = MatchResult(status="unknown")

    card = build_card(event, desc, match)
    assert card["severity"] == "info"
    assert card["headline"] == "Movement outside"


def test_card_quiet_hours_overrides_to_attention():
    event = {
        "requestId": "req_c4",
        "accountId": "acct_1",
        "type": "motion_detected",
        "deviceName": "Front Door",
        "timeLocal": "2026-10-20T23:45:00Z",  # 11:45 PM
    }
    desc = {"sentence": "A visitor is walking by the porch.", "visitors": [{"role": "unknown_adult"}]}
    match = MatchResult(status="expected", matched_label="Late Visitor")  # Even if expected!
    settings = {"quietHours": {"start": "22:00", "end": "06:00"}}

    card = build_card(event, desc, match, settings=settings)
    assert card["severity"] == "attention"
    assert "Night activity" in card["headline"]
