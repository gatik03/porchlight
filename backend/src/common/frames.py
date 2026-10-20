"""Frame acquisition strategies across Ring snapshot, video clip, and dashboard fallback."""

from __future__ import annotations

import io
import logging
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any, Dict, Optional

from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class FrameResult:
    source: str  # 'snapshot' | 'clip' | 'dashboard' | 'none'
    image_bytes: Optional[bytes] = None
    width_px: Optional[int] = None
    height_px: Optional[int] = None


def resize_frame_if_needed(image_bytes: bytes, max_long_side: int = 1024) -> bytes:
    """Resize image to max 1024px on the longest dimension to cut latency and Bedrock token cost."""
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            w, h = img.size
            if max(w, h) <= max_long_side:
                return image_bytes

            scale = max_long_side / float(max(w, h))
            new_size = (int(w * scale), int(h * scale))
            resized = img.resize(new_size, Image.Resampling.LANCZOS)
            output = io.BytesIO()
            img_format = img.format or "JPEG"
            resized.save(output, format=img_format, quality=85)
            return output.getvalue()
    except Exception as e:
        logger.warning("Frame resize failed, using original bytes: %s", e)
        return image_bytes


def get_frame(
    event: Dict[str, Any],
    ring_token: Optional[str] = None,
    dashboard_frame_bytes: Optional[bytes] = None
) -> FrameResult:
    """Acquire doorstep image frame in priority order.
    
    1. Ring Image Snapshot API (if token available)
    2. Media clip download (stubbed / placeholder fallback)
    3. Dashboard-captured live canvas frame (if supplied)
    4. None (degraded mode)
    """
    # 1. Try Ring Snapshot if token exists
    if ring_token:
        from .ring_client import RingClient
        client = RingClient()
        snapshot_bytes = client.get_snapshot(event.get("deviceId", ""), ring_token)
        if snapshot_bytes:
            processed = resize_frame_if_needed(snapshot_bytes)
            return FrameResult(source="snapshot", image_bytes=processed)

    # 2. Try dashboard-captured frame
    if dashboard_frame_bytes:
        processed = resize_frame_if_needed(dashboard_frame_bytes)
        return FrameResult(source="dashboard", image_bytes=processed)

    # 3. Degraded mode: no image
    return FrameResult(source="none", image_bytes=None)


def latest_frame_key(device_id: str) -> str:
    return f"frames/latest/{device_id}.jpg"


def load_latest_frame(bucket: str, region: str, device_id: str, max_age_s: int = 60) -> Optional[bytes]:
    """Return the dashboard-posted latest frame for a device if fresher than max_age_s, else None.

    Falls back to the `_any` key because the dashboard's device id may differ from Ring's.
    """
    import boto3

    s3 = boto3.client("s3", region_name=region)
    for dev in (device_id, "_any"):
        try:
            obj = s3.get_object(Bucket=bucket, Key=latest_frame_key(dev))
            if (datetime.now(timezone.utc) - obj["LastModified"]).total_seconds() <= max_age_s:
                return obj["Body"].read()
        except Exception:
            continue
    return None
