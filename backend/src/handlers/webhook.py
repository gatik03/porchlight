"""Webhook Lambda handler for Ring developer portal and partner API events."""

from __future__ import annotations

import base64
import json
import logging
from typing import Any, Dict

import boto3

from common.config import get_config
from common.normalize import to_normalized_event
from common.signature import verify_webhook_signature
from common.store import delete_dedupe, put_event_history, put_event_if_absent

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _get_header(headers: Dict[str, str], header_name: str) -> str | None:
    """Case-insensitive header retrieval."""
    if not headers:
        return None
    target = header_name.lower()
    for k, v in headers.items():
        if k.lower() == target:
            return v
    return None


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Process incoming Ring webhook POST requests.
    
    Guarantees response within < 1.0 second.
    Enforces HMAC signature verification on raw bytes, deduplicates via DynamoDB,
    and enqueues valid events to SQS.
    """
    config = get_config()
    headers = event.get("headers") or {}

    # 1. Read raw body bytes
    body_data = event.get("body")
    if body_data is None:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "missing body"}),
        }

    if event.get("isBase64Encoded", False):
        raw_body = base64.b64decode(body_data)
    elif isinstance(body_data, str):
        raw_body = body_data.encode("utf-8")
    else:
        raw_body = bytes(body_data)

    # 2. Extract and check X-Signature header
    signature_header = _get_header(headers, "x-signature")
    if not signature_header:
        logger.warning("Rejected webhook: missing X-Signature header")
        return {
            "statusCode": 401,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "missing signature"}),
        }

    # 3. Cryptographic signature check on raw bytes
    if not verify_webhook_signature(raw_body, signature_header, config.hmac_key):
        logger.warning("Rejected webhook: invalid HMAC signature")
        return {
            "statusCode": 401,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "invalid signature"}),
        }

    # 4. Parse JSON payload
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as e:
        logger.error("Failed to parse JSON body: %s", e)
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "malformed json"}),
        }

    # 5. Normalize event
    normalized = to_normalized_event(payload, raw_body=raw_body)
    request_id = normalized["requestId"]

    # 6. Deduplicate via DynamoDB conditional write
    try:
        is_new = put_event_if_absent(request_id, payload, ttl_seconds=259200)
        if not is_new:
            logger.info("Deduplicated duplicate webhook request_id=%s", request_id)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"ok": True, "duplicate": True}),
            }
    except Exception as e:
        logger.error("Deduplication error for request_id=%s: %s", request_id, e)
        # Any error after verification acknowledges with 200 so Ring does not retry indefinitely
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"ok": True, "error": "dedupe_fallback"}),
        }

    # 7. Route based on event type
    event_type = normalized["type"]
    if event_type in ("button_press", "motion_detected"):
        try:
            if not config.events_queue_url:
                raise RuntimeError("EVENTS_QUEUE_URL not configured")
            sqs = boto3.client("sqs", region_name=config.aws_region)
            sqs.send_message(
                QueueUrl=config.events_queue_url,
                MessageBody=json.dumps(normalized),
            )
            logger.info("Enqueued %s event to SQS request_id=%s", event_type, request_id)
        except Exception as e:
            logger.error("Failed to enqueue message to SQS: %s", e)
            # Non-2xx so Ring retries; the dedupe record must not block that retry
            try:
                delete_dedupe(request_id)
            except Exception as de:
                logger.error("Failed to clear dedupe record: %s", de)
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "enqueue failed"}),
            }
    else:
        # Unknown or informational events (device_online, etc.) are recorded but not sent to AI processor
        try:
            put_event_history(normalized)
            logger.info("Recorded non-alert event type=%s request_id=%s", event_type, request_id)
        except Exception as e:
            logger.error("Failed to record event history: %s", e)

    # 8. Fast return HTTP 200
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"ok": True}),
    }
