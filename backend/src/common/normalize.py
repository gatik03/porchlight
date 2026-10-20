"""Normalize Ring webhook payloads into internal NormalizedEvent data contract."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict


def to_normalized_event(payload: Dict[str, Any], raw_body: bytes | None = None) -> Dict[str, Any]:
    """Convert raw Ring webhook payload into NormalizedEvent dictionary.
    
    Handles both Ring JSON:API v1.1 structure and simplified simulator formats.
    """
    now_utc = datetime.now(timezone.utc).isoformat()

    # 1. Extract meta request_id and account_id
    meta = payload.get("meta", {})
    request_id = meta.get("request_id")
    account_id = meta.get("account_id")

    if not request_id:
        if raw_body:
            request_id = hashlib.sha256(raw_body).hexdigest()[:24]
        else:
            request_id = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]

    if not account_id:
        account_id = payload.get("account_id", "acct_default")

    # 2. Extract event attributes from data or top-level
    data = payload.get("data", {})
    if isinstance(data, dict):
        attributes = data.get("attributes", {})
        relationships = data.get("relationships", {})
        raw_event_type = attributes.get("event_type") or data.get("type") or payload.get("event_type")
        device_id = (
            attributes.get("device_id")
            or relationships.get("device", {}).get("data", {}).get("id")
            or payload.get("device_id", "dev_front_door")
        )
        event_id = data.get("id") or attributes.get("event_id") or payload.get("event_id")
        occurred_at = attributes.get("created_at") or payload.get("created_at") or now_utc
    else:
        raw_event_type = payload.get("event_type")
        device_id = payload.get("device_id", "dev_front_door")
        event_id = payload.get("event_id")
        occurred_at = payload.get("created_at") or now_utc

    # 3. Normalize event type
    raw_type_str = str(raw_event_type or "").lower()
    if any(k in raw_type_str for k in ("button_press", "ding", "doorbell", "press")):
        event_type = "button_press"
    elif any(k in raw_type_str for k in ("motion", "movement")):
        event_type = "motion_detected"
    elif "device_added" in raw_type_str:
        event_type = "device_added"
    elif "device_removed" in raw_type_str:
        event_type = "device_removed"
    elif "device_online" in raw_type_str:
        event_type = "device_online"
    elif "device_offline" in raw_type_str:
        event_type = "device_offline"
    else:
        event_type = "other"

    # Friendly device name fallback
    device_name = payload.get("device_name", "Front Door")

    return {
        "requestId": str(request_id),
        "accountId": str(account_id),
        "type": event_type,
        "deviceId": str(device_id),
        "deviceName": device_name,
        "eventId": str(event_id) if event_id else None,
        "occurredAt": occurred_at,
        "receivedAt": now_utc,
        "timeLocal": occurred_at,  # Converted to household timezone in processor
        "raw": payload,
    }
