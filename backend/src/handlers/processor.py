"""Processor Lambda: Consumes SQS events, fetches frames, invokes Bedrock vision, and persists Cards."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict

import boto3

from common.cards import build_card
from common.config import _get_ssm_parameter, get_config
from common.frames import get_frame, load_latest_frame
from common.matcher import match_expected
from common.store import get_household_settings, put_current_card, put_event_history
from common.vision import describe_frame

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _upload_frame_and_presign(
    image_bytes: bytes,
    account_id: str,
    request_id: str,
    bucket_name: str,
    region: str,
) -> str | None:
    """Upload doorstep frame to private S3 bucket and generate 1-hour presigned URL."""
    s3_key = f"frames/{account_id}/{request_id}.jpg"
    try:
        s3 = boto3.client("s3", region_name=region)
        s3.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=image_bytes,
            ContentType="image/jpeg",
        )
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": s3_key},
            ExpiresIn=3600,
        )
        return url
    except Exception as e:
        logger.warning("Failed to upload frame or generate presigned URL: %s", e)
        return None


def process_event(event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single NormalizedEvent message."""
    t_start = time.perf_counter()
    config = get_config()
    account_id = event_dict.get("accountId", "acct_default")
    request_id = event_dict.get("requestId", "req_unknown")

    # 1. Fetch household settings
    settings = get_household_settings(account_id)
    expected_visitors = settings.get("expectedVisitors", [])

    # 2. Acquire frame
    t_frame_start = time.perf_counter()
    ring_token = _get_ssm_parameter("/porchlight/ring/access_token")
    dashboard_bytes = load_latest_frame(
        config.frames_bucket_name, config.aws_region, event_dict.get("deviceId", "")
    )
    frame_res = get_frame(event_dict, ring_token=ring_token, dashboard_frame_bytes=dashboard_bytes)
    t_frame_end = time.perf_counter()

    # 3. Bedrock vision reasoning
    t_vision_start = time.perf_counter()
    context = {
        "eventType": event_dict.get("type", "button_press"),
        "deviceName": event_dict.get("deviceName", "Front Door"),
        "timeLocal": event_dict.get("timeLocal", "Today"),
        "expectedRoles": ", ".join(v.get("role", "") for v in expected_visitors) or "none",
        "expectedVisitors": expected_visitors,
    }
    desc = describe_frame(frame_res.image_bytes, context)
    t_vision_end = time.perf_counter()

    # 4. Match expected visitor schedule
    match = match_expected(desc, expected_visitors, event_dict.get("timeLocal", ""))

    # 5. Upload frame to S3 if available
    frame_url = None
    if frame_res.image_bytes and config.frames_bucket_name:
        frame_url = _upload_frame_and_presign(
            frame_res.image_bytes,
            account_id,
            request_id,
            config.frames_bucket_name,
            config.aws_region,
        )

    # 6. Build structured Card
    t_total = time.perf_counter() - t_start
    latency_ms = {
        "webhookToEnqueue": 150.0,
        "frame": round((t_frame_end - t_frame_start) * 1000, 1),
        "vision": round((t_vision_end - t_vision_start) * 1000, 1),
        "total": round(t_total * 1000, 1),
    }

    card = build_card(
        event=event_dict,
        desc=desc,
        match=match,
        settings=settings,
        frame_url=frame_url,
        latency_ms=latency_ms,
    )

    # 7. Persist to DynamoDB (current card + event history)
    put_current_card(card)
    put_event_history(event_dict, card)

    # 8. Emit structured latency log line
    log_data = {
        "metric": "porchlight_processing_latency",
        "requestId": request_id,
        "source": frame_res.source,
        "confidence": desc.get("confidence", 0.0),
        "matchStatus": match.status,
        "latencyMs": latency_ms,
    }
    logger.info("PROCESSED_EVENT %s", json.dumps(log_data))

    return card


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """SQS batch consumer entry point."""
    records = event.get("Records", [])
    processed_cards = []

    for record in records:
        body = record.get("body", "{}")
        try:
            event_data = json.loads(body)
            card = process_event(event_data)
            processed_cards.append(card)
        except Exception as e:
            logger.error("Failed processing SQS record %s: %s", record.get("messageId"), e)
            raise  # Let SQS redrive to DLQ after 3 failures

    return {"processed": len(processed_cards)}
