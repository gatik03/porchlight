"""Rule-based schedule and role matching for expected doorstep visitors."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class MatchResult:
    status: str  # 'expected' | 'unexpected' | 'unknown'
    matched_id: Optional[str] = None
    matched_label: Optional[str] = None
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "matchedId": self.matched_id,
            "matchedLabel": self.matched_label,
            "reason": self.reason,
        }


def _parse_time_parts(iso_or_time_str: str) -> tuple[str, str]:
    """Extract weekday ('mon'..'sun') and 'HH:MM' from ISO string."""
    try:
        # Handles ISO strings like 2026-10-18T10:04:12Z
        dt = datetime.fromisoformat(iso_or_time_str.replace("Z", "+00:00"))
        weekday_map = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        weekday = weekday_map[dt.weekday()]
        time_hm = dt.strftime("%H:%M")
        return weekday, time_hm
    except Exception:
        now = datetime.now()
        weekday_map = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        return weekday_map[now.weekday()], now.strftime("%H:%M")


def match_expected(
    visitor_desc: Dict[str, Any],
    expected_visitors: List[Dict[str, Any]],
    time_local_str: str
) -> MatchResult:
    """Evaluate whether visitor description matches household expected schedule.
    
    Zero facial recognition: uses recognized role, day of week, time window, and carries.
    """
    visitors = visitor_desc.get("visitors", [])
    if not visitors:
        return MatchResult(status="unknown", reason="No visitors detected in frame")

    weekday, current_time = _parse_time_parts(time_local_str)

    # Collect all detected roles and carrying items
    detected_roles = {v.get("role") for v in visitors if v.get("role")}
    detected_carries = {item.lower() for v in visitors for item in v.get("carrying", [])}

    for expected in expected_visitors:
        exp_id = expected.get("id")
        exp_label = expected.get("label", "Expected Visitor")
        exp_role = expected.get("role")
        exp_days = [d.lower() for d in expected.get("days", [])]
        start_time = expected.get("windowStart", "00:00")
        end_time = expected.get("windowEnd", "23:59")
        exp_carries = [c.lower() for c in expected.get("carries", [])]

        # 1. Day check
        if weekday not in exp_days:
            continue

        # 2. Time window check
        if not (start_time <= current_time <= end_time):
            continue

        # 3. Role check
        if exp_role in detected_roles:
            reason = (
                f"Matched {exp_label} ({exp_role}) on {weekday.capitalize()} "
                f"inside window {start_time}-{end_time}"
            )
            return MatchResult(
                status="expected",
                matched_id=exp_id,
                matched_label=exp_label,
                reason=reason,
            )

        # 4. Carries check (e.g. Courier with parcel)
        if exp_carries and any(c in detected_carries for c in exp_carries):
            reason = (
                f"Matched {exp_label} by carried item inside window {start_time}-{end_time}"
            )
            return MatchResult(
                status="expected",
                matched_id=exp_id,
                matched_label=exp_label,
                reason=reason,
            )

    return MatchResult(
        status="unexpected",
        reason=f"Visitor did not match any scheduled expected visitor for {weekday.capitalize()} at {current_time}",
    )
