"""Unit tests for Ring event normalization."""

from common.normalize import to_normalized_event


def test_normalize_button_press_json_api():
    payload = {
        "meta": {"request_id": "req_123", "account_id": "acct_456"},
        "data": {
            "type": "events",
            "id": "event_789",
            "attributes": {
                "event_type": "button_press",
                "device_id": "doorbell_front",
                "created_at": "2026-10-18T10:00:00Z",
            },
        },
    }
    normalized = to_normalized_event(payload)
    assert normalized["requestId"] == "req_123"
    assert normalized["accountId"] == "acct_456"
    assert normalized["type"] == "button_press"
    assert normalized["deviceId"] == "doorbell_front"
    assert normalized["eventId"] == "event_789"
    assert normalized["occurredAt"] == "2026-10-18T10:00:00Z"


def test_normalize_motion_detected_simplified():
    payload = {
        "event_type": "motion",
        "device_id": "cam_backyard",
        "created_at": "2026-10-18T11:30:00Z",
    }
    normalized = to_normalized_event(payload)
    assert normalized["type"] == "motion_detected"
    assert normalized["deviceId"] == "cam_backyard"
    assert normalized["requestId"] is not None
    assert len(normalized["requestId"]) > 0


def test_normalize_device_online():
    payload = {
        "meta": {"request_id": "req_online_1"},
        "data": {
            "attributes": {"event_type": "device_online", "device_id": "doorbell_front"}
        },
    }
    normalized = to_normalized_event(payload)
    assert normalized["type"] == "device_online"
    assert normalized["deviceId"] == "doorbell_front"


def test_normalize_unknown_type():
    payload = {
        "event_type": "firmware_update_completed",
        "device_id": "doorbell_front",
    }
    normalized = to_normalized_event(payload)
    assert normalized["type"] == "other"
