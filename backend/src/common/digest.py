"""Caretaker digest calculation, deterministic anomaly detection, and Bedrock narrative."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import boto3

from .config import get_config
from .prompts import DIGEST_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def detect_anomalies(
    events: List[Dict[str, Any]],
    baseline_median_buckets: Optional[Dict[str, int]] = None,
    settings: Optional[Dict[str, Any]] = None,
    date_str: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Deterministic rule-based anomaly detection.
    
    The AI model NEVER decides what is anomalous. Code evaluates rules against baseline.
    """
    settings = settings or {}
    quiet_hours = settings.get("quietHours", {"start": "22:00", "end": "06:00"})
    expected_visitors = settings.get("expectedVisitors", [])
    anomalies: List[Dict[str, str]] = []

    # Rule 1: Night activity in quiet hours
    q_start = quiet_hours.get("start", "22:00")
    q_end = quiet_hours.get("end", "06:00")
    for ev in events:
        time_str = ev.get("occurredAt", "")
        try:
            dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
            hm = dt.strftime("%H:%M")
            is_night = hm >= q_start or hm <= q_end if q_start > q_end else q_start <= hm <= q_end
            if is_night:
                ev_type = ev.get("type", "event")
                anomalies.append({
                    "kind": "night_activity",
                    "window": hm,
                    "explanation": f"Unexpected {ev_type} recorded during quiet hours at {hm}.",
                })
                break  # Record one night activity anomaly per day
        except Exception:
            continue

    # Rule 2: Quiet day anomaly (3-hour daytime bucket with 0 events when baseline >= 2)
    baseline = baseline_median_buckets or {"09-12": 3, "12-15": 2, "15-18": 2}
    buckets_count = {"09-12": 0, "12-15": 0, "15-18": 0}
    for ev in events:
        time_str = ev.get("occurredAt", "")
        try:
            dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
            hour = dt.hour
            if 9 <= hour < 12:
                buckets_count["09-12"] += 1
            elif 12 <= hour < 15:
                buckets_count["12-15"] += 1
            elif 15 <= hour < 18:
                buckets_count["15-18"] += 1
        except Exception:
            continue

    for bucket, count in buckets_count.items():
        median_expected = baseline.get(bucket, 0)
        if count == 0 and median_expected >= 2:
            anomalies.append({
                "kind": "quiet_day",
                "window": bucket,
                "explanation": f"Zero activity between {bucket.replace('-', ':00 and ')}:00, whereas baseline median is {median_expected} events.",
            })

    # Rule 3: Repeated unexpected visitor (>= 3 times)
    visitor_sentences: Dict[str, int] = {}
    for ev in events:
        card = ev.get("card")
        if card and card.get("severity") == "attention":
            sent = card.get("sentence", "").strip().lower()
            if sent:
                visitor_sentences[sent] = visitor_sentences.get(sent, 0) + 1

    for sent, freq in visitor_sentences.items():
        if freq >= 3:
            anomalies.append({
                "kind": "unexpected_repeat",
                "window": "all_day",
                "explanation": f"The same unexpected visitor pattern was recorded {freq} times today: '{sent}'.",
            })

    # Rule 4: Expected visitor scheduled today but no event carried their "Expected: <label>" line
    if date_str:
        weekday = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][datetime.strptime(date_str, "%Y-%m-%d").weekday()]
        seen = {(ev.get("card") or {}).get("expectedLine") for ev in events}
        for v in expected_visitors:
            label = v.get("label", "")
            if weekday in [d.lower() for d in v.get("days", [])] and f"Expected: {label}" not in seen:
                window = f"{v.get('windowStart', '00:00')}-{v.get('windowEnd', '23:59')}"
                anomalies.append({
                    "kind": "expected_missed",
                    "window": window,
                    "explanation": f"{label} was expected between {window} but no matching visit was recorded.",
                })

    return anomalies


def build_digest(
    account_id: str,
    date_str: str,
    events: List[Dict[str, Any]],
    settings: Optional[Dict[str, Any]] = None,
    bedrock_client: Optional[Any] = None,
) -> Dict[str, Any]:
    """Assemble full daily digest with metrics, rules, and optional Bedrock narration."""
    button_presses = sum(1 for e in events if e.get("type") == "button_press")
    motion_events = sum(1 for e in events if e.get("type") == "motion_detected")
    expected_matches = sum(
        1 for e in events if e.get("card", {}).get("severity") == "calm"
    )
    unexpected_matches = sum(
        1 for e in events if e.get("card", {}).get("severity") == "attention"
    )

    timeline = []
    for e in events:
        card = e.get("card")
        if card:
            timeline.append({
                "timeLocal": e.get("timeLocal", e.get("occurredAt", "")),
                "headline": card.get("headline", "Event"),
                "sentence": card.get("sentence", ""),
                "severity": card.get("severity", "info"),
            })

    anomalies = detect_anomalies(events, settings=settings, date_str=date_str)

    # Generate Bedrock narrative or fallback
    narrative = narrate_digest(timeline, anomalies, bedrock_client=bedrock_client)

    now_iso = datetime.now().isoformat()
    return {
        "accountId": account_id,
        "date": date_str,
        "timeline": timeline,
        "counts": {
            "buttonPresses": button_presses,
            "motion": motion_events,
            "expected": expected_matches,
            "unexpected": unexpected_matches,
        },
        "anomalies": anomalies,
        "narrative": narrative,
        "builtAt": now_iso,
    }


def narrate_digest(
    timeline: List[Dict[str, Any]],
    anomalies: List[Dict[str, str]],
    bedrock_client: Optional[Any] = None,
) -> str:
    """Invoke Bedrock text model to write warm <= 120-word summary."""
    config = get_config()
    client = bedrock_client or boto3.client("bedrock-runtime", region_name=config.aws_region)

    timeline_summary = "\n".join(
        f"- {item.get('timeLocal')}: {item.get('headline')} ({item.get('sentence')})"
        for item in timeline[-10:]
    )
    anomaly_summary = "\n".join(
        f"- {a.get('kind')}: {a.get('explanation')}" for a in anomalies
    ) or "None"

    user_text = (
        f"Timeline of doorstep events:\n{timeline_summary or 'No events today.'}\n\n"
        f"Detected anomalies:\n{anomaly_summary}"
    )

    try:
        response = client.converse(
            modelId=config.bedrock_text_model_id,
            messages=[{"role": "user", "content": [{"text": user_text}]}],
            system=[{"text": DIGEST_SYSTEM_PROMPT}],
            inferenceConfig={"temperature": 0.2, "maxTokens": 200},
        )
        content = response.get("output", {}).get("message", {}).get("content", [])
        narrative = "".join(b.get("text", "") for b in content if "text" in b).strip()
        words = narrative.split()
        if len(words) > 130:
            narrative = " ".join(words[:120]) + "..."
        return narrative
    except Exception as e:
        logger.warning("Bedrock text narration failed: %s. Using rule-based fallback.", e)
        if not anomalies:
            return (
                f"Today at the front door was normal with {len(timeline)} recorded events. "
                "All expected visitors arrived on schedule with no unexpected night activity."
            )
        anomaly_desc = "; ".join(a["explanation"] for a in anomalies)
        return (
            f"Activity summary: {len(timeline)} events recorded. "
            f"Please note the following doorstep patterns today: {anomaly_desc}."
        )
