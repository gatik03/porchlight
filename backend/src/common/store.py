"""DynamoDB single-table operations for Porchlight."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from .config import get_config


def _get_table():
    config = get_config()
    dynamodb = boto3.resource("dynamodb", region_name=config.aws_region)
    return dynamodb.Table(config.table_name)


def put_event_if_absent(
    request_id: str,
    raw_event: Dict[str, Any],
    ttl_seconds: int = 259200
) -> bool:
    """Conditionally store an event deduplication record in DynamoDB.
    
    Returns:
        True if the item was newly inserted (first time seeing this request_id).
        False if the item already exists (duplicate webhook).
    """
    table = _get_table()
    now_ts = int(time.time())
    ttl = now_ts + ttl_seconds

    try:
        table.put_item(
            Item={
                "pk": f"DEDUPE#{request_id}",
                "sk": "x",
                "requestId": request_id,
                "receivedAt": datetime.now(timezone.utc).isoformat(),
                "ttl": ttl,
            },
            ConditionExpression="attribute_not_exists(pk)",
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise


def delete_dedupe(request_id: str) -> None:
    """Remove a dedupe record so a Ring retry of a failed enqueue is processed."""
    _get_table().delete_item(Key={"pk": f"DEDUPE#{request_id}", "sk": "x"})


from decimal import Decimal

def _sanitize_for_dynamodb(data: Any) -> Any:
    """Recursively convert float to Decimal and strip None for DynamoDB serialization."""
    if isinstance(data, float):
        return Decimal(str(data))
    if isinstance(data, dict):
        return {k: _sanitize_for_dynamodb(v) for k, v in data.items() if v is not None}
    if isinstance(data, list):
        return [_sanitize_for_dynamodb(v) for v in data]
    return data


def put_current_card(card: Dict[str, Any]) -> None:
    """Store or overwrite the current active card for an account."""
    table = _get_table()
    account_id = card["accountId"]
    item = _sanitize_for_dynamodb(dict(card))
    item["pk"] = f"CURRENT#{account_id}"
    item["sk"] = "card"
    table.put_item(Item=item)


def get_current_card(account_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve the current active card for an account."""
    table = _get_table()
    res = table.get_item(Key={"pk": f"CURRENT#{account_id}", "sk": "card"})
    return res.get("Item")


def mark_card_dismissed(account_id: str) -> bool:
    """Mark the current card as dismissed."""
    table = _get_table()
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        table.update_item(
            Key={"pk": f"CURRENT#{account_id}", "sk": "card"},
            UpdateExpression="SET dismissedAt = :now",
            ExpressionAttributeValues={":now": now_iso},
            ConditionExpression="attribute_exists(pk)",
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise


def put_event_history(event: Dict[str, Any], card: Optional[Dict[str, Any]] = None) -> None:
    """Store an event and its associated card in the 30-day event history."""
    table = _get_table()
    account_id = event["accountId"]
    occurred_at = event.get("occurredAt", datetime.now(timezone.utc).isoformat())
    request_id = event["requestId"]
    ttl = int(time.time()) + (30 * 86400)

    item: Dict[str, Any] = {
        "pk": f"EVENT#{account_id}",
        "sk": f"{occurred_at}#{request_id}",
        "requestId": request_id,
        "type": event["type"],
        "deviceId": event["deviceId"],
        "deviceName": event.get("deviceName", "Front Door"),
        "occurredAt": occurred_at,
        "ttl": ttl,
    }
    if card:
        item["card"] = _sanitize_for_dynamodb(card)
    table.put_item(Item=item)


def get_events_for_date(account_id: str, date_str: str) -> List[Dict[str, Any]]:
    """Query events for an account on a given YYYY-MM-DD date."""
    table = _get_table()
    start_sk = f"{date_str}T00:00:00"
    end_sk = f"{date_str}T23:59:59~"

    from boto3.dynamodb.conditions import Key

    res = table.query(
        KeyConditionExpression=Key("pk").eq(f"EVENT#{account_id}") & Key("sk").between(start_sk, end_sk)
    )
    return res.get("Items", [])


def get_household_settings(account_id: str) -> Dict[str, Any]:
    """Retrieve household settings with safe accessibility defaults."""
    table = _get_table()
    res = table.get_item(Key={"pk": f"SETTINGS#{account_id}", "sk": "x"})
    item = res.get("Item")
    if not item:
        # Default fallback settings
        return {
            "accountId": account_id,
            "timezone": "America/Los_Angeles",
            "deviceNames": {"dev_front_door": "Front Door"},
            "expectedVisitors": [],
            "quietHours": {"start": "22:00", "end": "06:00"},
            "flashIntensity": "high",
        }
    return item


def put_household_settings(account_id: str, settings: Dict[str, Any]) -> None:
    """Save household settings."""
    table = _get_table()
    item = dict(settings)
    item["pk"] = f"SETTINGS#{account_id}"
    item["sk"] = "x"
    table.put_item(Item=item)


def put_digest(digest: Dict[str, Any]) -> None:
    """Store daily caregiver digest."""
    table = _get_table()
    item = dict(digest)
    item["pk"] = f"DIGEST#{digest['accountId']}"
    item["sk"] = digest["date"]
    table.put_item(Item=item)


def get_digest(account_id: str, date_str: str) -> Optional[Dict[str, Any]]:
    """Retrieve stored daily caregiver digest."""
    table = _get_table()
    res = table.get_item(Key={"pk": f"DIGEST#{account_id}", "sk": date_str})
    return res.get("Item")
