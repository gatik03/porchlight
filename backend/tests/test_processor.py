"""Integration tests for Processor Lambda handler."""

import json

from handlers.processor import lambda_handler
from common.store import get_current_card


def test_processor_handles_sqs_event(mock_dynamodb, mock_sqs, mock_s3):
    normalized_event = {
        "requestId": "req_proc_01",
        "accountId": "acct_proc_test",
        "type": "button_press",
        "deviceId": "doorbell_front",
        "deviceName": "Front Door",
        "occurredAt": "2026-10-20T10:04:00Z",
        "receivedAt": "2026-10-20T10:04:01Z",
        "timeLocal": "2026-10-20T10:04:00Z",
    }

    sqs_event = {
        "Records": [
            {
                "messageId": "msg_001",
                "body": json.dumps(normalized_event),
            }
        ]
    }

    res = lambda_handler(sqs_event, None)
    assert res["processed"] == 1

    # Verify Card was written to DynamoDB CURRENT#acct_proc_test
    card = get_current_card("acct_proc_test")
    assert card is not None
    assert card["cardId"] == "req_proc_01"
    assert card["severity"] == "attention"
    assert "doorbell" in card["sentence"].lower() or "someone" in card["sentence"].lower()
