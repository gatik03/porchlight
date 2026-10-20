"""Integration tests for Read API Lambda handler."""

import json

from handlers.read_api import lambda_handler
from common.store import put_current_card


def test_read_api_health_public():
    event = {
        "requestContext": {"http": {"method": "GET", "path": "/api/health"}},
        "headers": {},
    }
    res = lambda_handler(event, None)
    assert res["statusCode"] == 200
    body = json.loads(res["body"])
    assert body["ok"] is True
    assert body["service"] == "porchlight"


def test_read_api_unauthorized_without_passphrase():
    event = {
        "requestContext": {"http": {"method": "GET", "path": "/api/settings"}},
        "headers": {},
    }
    res = lambda_handler(event, None)
    assert res["statusCode"] == 401


def test_read_api_settings_lifecycle(mock_dynamodb):
    # GET settings
    get_event = {
        "requestContext": {"http": {"method": "GET", "path": "/api/settings"}},
        "headers": {"x-porchlight-key": "test-dashboard-passphrase"},
    }
    res = lambda_handler(get_event, None)
    assert res["statusCode"] == 200
    settings = json.loads(res["body"])
    assert settings["flashIntensity"] == "high"

    # PUT settings
    settings["flashIntensity"] = "low"
    put_event = {
        "requestContext": {"http": {"method": "PUT", "path": "/api/settings"}},
        "headers": {"x-porchlight-key": "test-dashboard-passphrase"},
        "body": json.dumps(settings),
    }
    put_res = lambda_handler(put_event, None)
    assert put_res["statusCode"] == 200

    # Verify update
    verify_res = lambda_handler(get_event, None)
    assert json.loads(verify_res["body"])["flashIntensity"] == "low"


def test_read_api_current_card_and_dismiss(mock_dynamodb):
    # When no card exists -> 204
    get_event = {
        "requestContext": {"http": {"method": "GET", "path": "/api/card/current"}},
        "headers": {"x-porchlight-key": "test-dashboard-passphrase"},
    }
    empty_res = lambda_handler(get_event, None)
    assert empty_res["statusCode"] == 204

    # Seed card
    card = {
        "cardId": "req_api_1",
        "accountId": "acct_demo_household",
        "severity": "attention",
        "headline": "Someone is at the door",
        "sentence": "A courier is holding a parcel.",
        "deviceName": "Front Door",
        "timeLocal": "2026-10-20T10:04:00Z",
        "createdAt": "2026-10-20T10:04:00Z",
    }
    put_current_card(card)

    card_res = lambda_handler(get_event, None)
    assert card_res["statusCode"] == 200
    card_body = json.loads(card_res["body"])
    assert card_body["cardId"] == "req_api_1"

    # Dismiss card
    dismiss_event = {
        "requestContext": {"http": {"method": "POST", "path": "/api/card/dismiss"}},
        "headers": {"x-porchlight-key": "test-dashboard-passphrase"},
    }
    dismiss_res = lambda_handler(dismiss_event, None)
    assert dismiss_res["statusCode"] == 200

    # After dismissal -> 204
    after_dismiss_res = lambda_handler(get_event, None)
    assert after_dismiss_res["statusCode"] == 204


def _req(method, path, body=None):
    return {
        "requestContext": {"http": {"method": method, "path": path}},
        "headers": {"x-porchlight-key": "test-dashboard-passphrase"},
        "body": json.dumps(body) if body is not None else None,
    }


def test_post_frame_stored_and_loaded(mock_s3):
    import base64
    from common.frames import load_latest_frame

    frame = "data:image/jpeg;base64," + base64.b64encode(b"jpegbytes").decode()
    res = lambda_handler(_req("POST", "/api/frames", {"frame": frame, "deviceId": "dev_front"}), None)
    assert res["statusCode"] == 200
    assert load_latest_frame("porchlight-frames", "us-east-1", "dev_front") == b"jpegbytes"
    assert load_latest_frame("porchlight-frames", "us-east-1", "other_dev") == b"jpegbytes"  # _any fallback
    assert lambda_handler(_req("POST", "/api/frames", {"frame": frame, "deviceId": "../x"}), None)["statusCode"] == 400


def test_get_digest(mock_dynamodb):
    from common.store import put_digest

    put_digest({"accountId": "acct_demo_household", "date": "2026-10-18", "timeline": [], "anomalies": []})
    ok = lambda_handler(_req("GET", "/api/digest/2026-10-18"), None)
    assert ok["statusCode"] == 200 and json.loads(ok["body"])["date"] == "2026-10-18"
    assert lambda_handler(_req("GET", "/api/digest/2026-10-19"), None)["statusCode"] == 404
