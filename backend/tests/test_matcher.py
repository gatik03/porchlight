"""Unit tests for visitor schedule and role matching."""

from common.matcher import match_expected


def test_matcher_expected_visitor_in_window():
    visitor_desc = {
        "visitors": [{"role": "service_worker", "carrying": ["toolbox"]}],
        "sentence": "A service worker with a toolbox is at the door.",
    }
    expected_visitors = [
        {
            "id": "v1",
            "label": "Nurse Priya",
            "role": "service_worker",
            "days": ["tue", "thu"],
            "windowStart": "09:30",
            "windowEnd": "11:00",
        }
    ]
    # Tuesday 10:04 AM UTC
    time_str = "2026-10-20T10:04:00Z"  # 2026-10-20 is a Tuesday

    res = match_expected(visitor_desc, expected_visitors, time_str)
    assert res.status == "expected"
    assert res.matched_id == "v1"
    assert res.matched_label == "Nurse Priya"


def test_matcher_expected_visitor_wrong_day():
    visitor_desc = {
        "visitors": [{"role": "service_worker", "carrying": []}],
    }
    expected_visitors = [
        {
            "id": "v1",
            "label": "Nurse Priya",
            "role": "service_worker",
            "days": ["tue", "thu"],
            "windowStart": "09:30",
            "windowEnd": "11:00",
        }
    ]
    # Wednesday 10:04 AM UTC
    time_str = "2026-10-21T10:04:00Z"  # 2026-10-21 is a Wednesday

    res = match_expected(visitor_desc, expected_visitors, time_str)
    assert res.status == "unexpected"


def test_matcher_expected_visitor_outside_window():
    visitor_desc = {
        "visitors": [{"role": "service_worker", "carrying": []}],
    }
    expected_visitors = [
        {
            "id": "v1",
            "label": "Nurse Priya",
            "role": "service_worker",
            "days": ["tue", "thu"],
            "windowStart": "09:30",
            "windowEnd": "11:00",
        }
    ]
    # Tuesday 15:30 (3:30 PM)
    time_str = "2026-10-20T15:30:00Z"

    res = match_expected(visitor_desc, expected_visitors, time_str)
    assert res.status == "unexpected"


def test_matcher_no_visitors_detected():
    visitor_desc = {
        "visitors": [],
        "sentence": "A car is driving by the front porch.",
    }
    res = match_expected(visitor_desc, [], "2026-10-20T10:00:00Z")
    assert res.status == "unknown"


def test_matcher_carried_item_bonus_match():
    visitor_desc = {
        "visitors": [{"role": "unknown_adult", "carrying": ["parcel", "package"]}],
    }
    expected_visitors = [
        {
            "id": "v_courier",
            "label": "Package Delivery",
            "role": "courier",
            "days": ["mon", "tue", "wed", "thu", "fri"],
            "windowStart": "08:00",
            "windowEnd": "18:00",
            "carries": ["parcel"],
        }
    ]
    time_str = "2026-10-20T14:00:00Z"
    res = match_expected(visitor_desc, expected_visitors, time_str)
    assert res.status == "expected"
    assert res.matched_id == "v_courier"
