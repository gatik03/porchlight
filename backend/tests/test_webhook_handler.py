"""Integration tests for Webhook Lambda handler."""

import json

from common.signature import compute_webhook_signature
from handlers.webhook import lambda_handler


def test_webhook_missing_body():
    event = {"headers": {"X-Signature": "sig123"}}
    res = lambda_handler(event, None)
    assert res["statusCode"] == 400


def test_webhook_missing_signature():
    event = {
        "headers": {},
        "body": '{"meta": {"request_id": "r1"}}',
    }
    res = lambda_handler(event, None)
    assert res["statusCode"] == 401
    assert "missing signature" in res["body"]


def test_webhook_invalid_signature():
    event = {
        "headers": {"X-Signature": "invalid_sig"},
        "body": '{"meta": {"request_id": "r1"}}',
    }
    res = lambda_handler(event, None)
    assert res["statusCode"] == 401
    assert "invalid signature" in res["body"]


def test_webhook_valid_button_press(mock_dynamodb, mock_sqs):
    body_str = json.dumps({
        "meta": {"request_id": "req_wb_1", "account_id": "acct_test"},
        "data": {
            "attributes": {
                "event_type": "button_press",
                "device_id": "doorbell_front",
                "created_at": "2026-10-18T10:00:00Z",
            }
        },
    })
    body_bytes = body_str.encode("utf-8")
    sig = compute_webhook_signature(body_bytes, "test-secret-hmac-key")

    event = {
        "headers": {"X-Signature": sig},
        "body": body_str,
        "isBase64Encoded": False,
    }

    res = lambda_handler(event, None)
    assert res["statusCode"] == 200
    assert json.loads(res["body"]) == {"ok": True}

    # Verify deduplication: second exact call returns duplicate True
    res_duplicate = lambda_handler(event, None)
    assert res_duplicate["statusCode"] == 200
    assert json.loads(res_duplicate["body"]) == {"ok": True, "duplicate": True}


def test_webhook_unknown_event_not_enqueued(mock_dynamodb, mock_sqs):
    body_str = json.dumps({
        "meta": {"request_id": "req_wb_offline"},
        "data": {
            "attributes": {
                "event_type": "device_offline",
                "device_id": "doorbell_front",
            }
        },
    })
    body_bytes = body_str.encode("utf-8")
    sig = compute_webhook_signature(body_bytes, "test-secret-hmac-key")

    event = {
        "headers": {"x-signature": sig},
        "body": body_str,
    }

    res = lambda_handler(event, None)
    assert res["statusCode"] == 200
    assert json.loads(res["body"]) == {"ok": True}


def test_webhook_returns_500_when_enqueue_fails(mock_dynamodb, monkeypatch):
    from common.config import get_config

    body_str = json.dumps({
        "meta": {"request_id": "req_wb_fail", "account_id": "acct_test"},
        "data": {"attributes": {"event_type": "button_press", "device_id": "doorbell_front"}},
    })
    sig = compute_webhook_signature(body_str.encode("utf-8"), "test-secret-hmac-key")
    event = {"headers": {"x-signature": sig}, "body": body_str}
    monkeypatch.setattr("handlers.webhook.get_config", lambda: get_config().__class__(**{**get_config().__dict__, "events_queue_url": ""}))

    assert lambda_handler(event, None)["statusCode"] == 500
    # dedupe record cleared so Ring's retry is processed, not dropped
    assert lambda_handler(event, None)["statusCode"] == 500
