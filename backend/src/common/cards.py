"""Card builder and severity decision engine for Porchlight."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .matcher import MatchResult


def _is_in_quiet_hours(time_str: str, quiet_hours: Dict[str, str]) -> bool:
    """Check if time falls within quiet hours (e.g. 22:00 to 06:00)."""
    start = quiet_hours.get("start", "22:00")
    end = quiet_hours.get("end", "06:00")
    try:
        dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        current_hm = dt.strftime("%H:%M")
    except Exception:
        current_hm = "12:00"

    if start > end:
        # Crosses midnight: e.g. 22:00 to 06:00
        return current_hm >= start or current_hm <= end
    return start <= current_hm <= end


def build_card(
    event: Dict[str, Any],
    desc: Dict[str, Any],
    match: MatchResult,
    settings: Optional[Dict[str, Any]] = None,
    frame_url: Optional[str] = None,
    latency_ms: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Construct a full Card object with strict severity rules."""
    settings = settings or {}
    quiet_hours = settings.get("quietHours", {"start": "22:00", "end": "06:00"})
    time_local = event.get("timeLocal") or event.get("occurredAt") or datetime.now(timezone.utc).isoformat()
    event_type = event.get("type", "button_press")
    visitors = desc.get("visitors", [])
    sentence = desc.get("sentence", "Someone is at the door.")

    in_quiet = _is_in_quiet_hours(time_local, quiet_hours)

    # Severity decision hierarchy
    if match.status == "expected" and not in_quiet:
        severity = "calm"
        headline = "Expected visitor"
    elif in_quiet:
        severity = "attention"
        headline = "Night activity at the door"
    elif event_type == "button_press":
        severity = "attention"
        headline = "Someone is at the door"
    elif event_type == "motion_detected":
        if visitors:
            severity = "attention"
            headline = "Unexpected visitor outside"
        else:
            severity = "info"
            headline = "Movement outside"
    else:
        severity = "info"
        headline = "Activity detected"

    # Expected visitor line
    expected_line = None
    if match.matched_label:
        expected_line = f"Expected: {match.matched_label}"

    now_utc = datetime.now(timezone.utc).isoformat()

    return {
        "cardId": event["requestId"],
        "accountId": event["accountId"],
        "severity": severity,
        "headline": headline,
        "sentence": sentence,
        "expectedLine": expected_line,
        "deviceName": event.get("deviceName", "Front Door"),
        "timeLocal": time_local,
        "frameUrl": frame_url,
        "createdAt": now_utc,
        "dismissedAt": None,
        "latencyMs": latency_ms or {"webhookToEnqueue": 0, "frame": 0, "vision": 0, "total": 0},
    }
