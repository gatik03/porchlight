#!/usr/bin/env python3
"""Seed historical doorstep events into DynamoDB for Caretaker Digest demo."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add backend/src to sys.path
SRC_DIR = str(Path(__file__).resolve().parents[2] / "backend" / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from common.store import put_event_history


def seed_history(account_id: str, days: int = 14) -> None:
    print(f"Seeding {days} days of historical events for account '{account_id}'...")
    now = datetime.now(timezone.utc)

    event_patterns = [
        {"type": "motion_detected", "hour": 10, "minute": 15, "headline": "Movement outside", "sentence": "A neighbor walked past the front garden."},
        {"type": "button_press", "hour": 11, "minute": 30, "headline": "Expected visitor", "sentence": "Nurse arrived for scheduled physical checkup.", "severity": "calm"},
        {"type": "motion_detected", "hour": 14, "minute": 0, "headline": "Movement outside", "sentence": "Postal carrier delivered letters to mailbox."},
        {"type": "button_press", "hour": 16, "minute": 45, "headline": "Someone is at the door", "sentence": "A courier dropped off a package on the porch.", "severity": "attention"},
    ]

    count = 0
    for day_offset in range(1, days + 1):
        target_date = now - timedelta(days=day_offset)
        for pattern in event_patterns:
            event_dt = target_date.replace(hour=pattern["hour"], minute=pattern["minute"], second=0)
            iso_str = event_dt.isoformat()
            req_id = f"seed_{target_date.strftime('%Y%m%d')}_{pattern['hour']}{pattern['minute']}"

            event = {
                "requestId": req_id,
                "accountId": account_id,
                "type": pattern["type"],
                "deviceId": "doorbell_front",
                "deviceName": "Front Door",
                "occurredAt": iso_str,
                "timeLocal": iso_str,
            }

            card = {
                "cardId": req_id,
                "accountId": account_id,
                "severity": pattern.get("severity", "info"),
                "headline": pattern["headline"],
                "sentence": pattern["sentence"],
                "deviceName": "Front Door",
                "timeLocal": iso_str,
                "createdAt": iso_str,
            }

            try:
                put_event_history(event, card)
                count += 1
            except Exception as e:
                print(f"Error seeding event: {e}")

    print(f"Successfully seeded {count} events across {days} days!")


def main():
    parser = argparse.ArgumentParser(description="Seed DynamoDB history for Caretaker Digest")
    parser.add_argument("--account", default="acct_demo_household", help="Account ID")
    parser.add_argument("--days", type=int, default=14, help="Number of days of history")
    args = parser.parse_args()

    seed_history(args.account, args.days)


if __name__ == "__main__":
    main()
