"""Client for Ring Partner API interactions (OAuth, Snapshots, Media)."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
import requests

logger = logging.getLogger(__name__)

RING_API_BASE = "https://api.amazonvision.com"


class RingClient:
    """Interface to Ring Partner API."""

    def __init__(self, client_id: str = "", client_secret: str = ""):
        self.client_id = client_id
        self.client_secret = client_secret

    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh OAuth access token using refresh_token grant."""
        url = f"{RING_API_BASE}/v1/oauth/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        try:
            res = requests.post(url, data=data, timeout=8)
            if res.status_code == 200:
                return res.json()
            logger.error("Token refresh failed: HTTP %s - %s", res.status_code, res.text)
            return None
        except Exception as e:
            logger.error("Token refresh network exception: %s", e)
            return None

    def get_snapshot(self, device_id: str, access_token: str) -> Optional[bytes]:
        """Fetch real-time or recent image snapshot for a device."""
        if not access_token or not device_id:
            return None

        # Check Ring Partner API snapshot endpoint
        url = f"{RING_API_BASE}/v1/devices/{device_id}/media/snapshot"
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            res = requests.get(url, headers=headers, timeout=6)
            if res.status_code == 200 and res.content:
                return res.content
            logger.warning("Snapshot API returned HTTP %s for device %s", res.status_code, device_id)
            return None
        except Exception as e:
            logger.warning("Snapshot API error for device %s: %s", device_id, e)
            return None

    def download_clip(self, device_id: str, event_id: str, access_token: str) -> Optional[bytes]:
        """Download historical video clip for an event."""
        if not access_token or not device_id or not event_id:
            return None

        url = f"{RING_API_BASE}/v1/devices/{device_id}/media/video/download"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        payload = {"event_id": event_id}
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=10)
            if res.status_code == 200 and res.content:
                return res.content
            return None
        except Exception as e:
            logger.warning("Clip download error for event %s: %s", event_id, e)
            return None
