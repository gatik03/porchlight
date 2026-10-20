"""Read API Lambda handler serving cards, events, settings, digests, and dashboard frames."""

from __future__ import annotations

import base64
import hmac
import json
import logging
import re
from decimal import Decimal
from typing import Any, Dict

import boto3

from common.config import get_config
from common.frames import latest_frame_key
from common.store import (
    get_digest,
    get_current_card,
    get_events_for_date,
    get_household_settings,
    mark_card_dismissed,
    put_household_settings,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DecimalEncoder(json.JSONEncoder):
    """Serialize Decimal objects to float/int for JSON responses."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super().default(obj)


def _json_response(status_code: int, body_dict: Any) -> Dict[str, Any]:
    """Format standardized API Gateway HTTP API response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,x-porchlight-key,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,OPTIONS",
        },
        "body": json.dumps(body_dict, cls=DecimalEncoder),
    }


def _get_header(headers: Dict[str, str], header_name: str) -> str | None:
    if not headers:
        return None
    target = header_name.lower()
    for k, v in headers.items():
        if k.lower() == target:
            return v
    return None


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Dispatch HTTP requests across /api/* routes."""
    config = get_config()
    request_context = event.get("requestContext", {}).get("http", {})
    method = request_context.get("method", event.get("httpMethod", "GET")).upper()
    path = request_context.get("path", event.get("path", "/api/health"))
    headers = event.get("headers") or {}
    query_params = event.get("queryStringParameters") or {}

    # Health check is public (no passphrase required)
    if path == "/api/health" or path.endswith("/health"):
        return _json_response(200, {"ok": True, "version": "1.0.0", "service": "porchlight"})

    # Check passphrase authentication
    auth_header = _get_header(headers, "x-porchlight-key")
    if not auth_header or not hmac.compare_digest(auth_header.encode(), config.dashboard_passphrase.encode()):
        return _json_response(401, {"error": "unauthorized"})

    account_id = "acct_demo_household"

    try:
        # Route 1: GET /api/card/current
        if path.startswith("/api/card/current") and method == "GET":
            since_time = query_params.get("since")
            card = get_current_card(account_id)

            if not card or card.get("dismissedAt"):
                return {"statusCode": 204, "headers": {"Content-Type": "application/json"}, "body": ""}

            if since_time and card.get("createdAt") and card["createdAt"] <= since_time:
                return {"statusCode": 204, "headers": {"Content-Type": "application/json"}, "body": ""}

            return _json_response(200, card)

        # Route 2: POST /api/card/dismiss
        if path.startswith("/api/card/dismiss") and method == "POST":
            mark_card_dismissed(account_id)
            return _json_response(200, {"ok": True})

        # Route 3: GET /api/events
        if path.startswith("/api/events") and method == "GET":
            date_str = query_params.get("date")
            if not date_str:
                from datetime import datetime
                date_str = datetime.now().strftime("%Y-%m-%d")
            events = get_events_for_date(account_id, date_str)
            return _json_response(200, {"events": events})

        # Route 4: GET /api/settings
        if path.startswith("/api/settings") and method == "GET":
            settings = get_household_settings(account_id)
            return _json_response(200, settings)

        # Route 5: PUT /api/settings
        if path.startswith("/api/settings") and method == "PUT":
            body_str = event.get("body", "{}")
            new_settings = json.loads(body_str) if isinstance(body_str, str) else body_str
            new_settings["accountId"] = account_id
            put_household_settings(account_id, new_settings)
            return _json_response(200, {"ok": True})

        # Route 7: GET /api/digest/{date}
        if path.startswith("/api/digest/") and method == "GET":
            date_str = path.rsplit("/", 1)[-1]
            digest = get_digest(account_id, date_str) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str) else None
            if not digest:
                return _json_response(404, {"error": "digest not found", "date": date_str})
            digest.pop("pk", None)
            digest.pop("sk", None)
            return _json_response(200, digest)

        # Route 6: POST /api/frames (Dashboard-captured live view frame)
        if path.startswith("/api/frames") and method == "POST":
            body_str = event.get("body") or "{}"
            if event.get("isBase64Encoded"):
                body_str = base64.b64decode(body_str).decode("utf-8")
            body = json.loads(body_str) if isinstance(body_str, str) else body_str
            device_id = str(body.get("deviceId", ""))
            frame = str(body.get("frame", ""))
            if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", device_id) or not frame:
                return _json_response(400, {"error": "deviceId and frame required"})
            try:
                image = base64.b64decode(frame.split(",", 1)[-1], validate=True)
            except Exception:
                return _json_response(400, {"error": "frame must be base64 jpeg"})
            s3 = boto3.client("s3", region_name=config.aws_region)
            # _any: processor fallback when dashboard and Ring device ids differ
            for dev in (device_id, "_any"):
                s3.put_object(
                    Bucket=config.frames_bucket_name,
                    Key=latest_frame_key(dev),
                    Body=image,
                    ContentType="image/jpeg",
                )
            return _json_response(200, {"ok": True, "source": "dashboard"})

        return _json_response(404, {"error": "not found", "path": path})

    except Exception as e:
        logger.error("Read API error handling %s %s: %s", method, path, e)
        return _json_response(500, {"error": "internal server error"})
