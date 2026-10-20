#!/usr/bin/env python3
"""Interactive CLI utility to label new doorstep frames into fixtures/frames/labels.json."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ALLOWED_ROLES = [
    "courier",
    "delivery_food",
    "service_worker",
    "neighbor_or_friend",
    "solicitor",
    "child",
    "unknown_adult",
    "animal",
    "vehicle_only",
]

ALLOWED_INTENTS = [
    "delivery",
    "visit",
    "service",
    "sales_or_canvassing",
    "passing_by",
    "unknown",
]


def label_frame_interactive():
    root = Path(__file__).resolve().parents[2]
    labels_file = root / "fixtures" / "frames" / "labels.json"
    frames_dir = root / "fixtures" / "frames"

    if len(sys.argv) < 2:
        print("Usage: python label_frames.py <path_to_image.jpg>")
        return 1

    src_image = Path(sys.argv[1])
    if not src_image.is_file():
        print(f"Error: image file not found: {src_image}")
        return 1

    labels = []
    if labels_file.is_file():
        labels = json.loads(labels_file.read_text(encoding="utf-8"))

    print(f"\n--- Labeling Frame: {src_image.name} ---")
    desc = input("1. Description (e.g. Courier with box): ").strip()

    print("\nAllowed Roles:")
    for i, r in enumerate(ALLOWED_ROLES, 1):
        print(f"  {i}. {r}")
    role_idx = int(input(f"Select Role (1-{len(ALLOWED_ROLES)}): ").strip()) - 1
    role = ALLOWED_ROLES[role_idx]

    print("\nAllowed Intents:")
    for i, intent in enumerate(ALLOWED_INTENTS, 1):
        print(f"  {i}. {intent}")
    intent_idx = int(input(f"Select Intent (1-{len(ALLOWED_INTENTS)}): ").strip()) - 1
    intent = ALLOWED_INTENTS[intent_idx]

    carries_str = input("\nCarried items (comma-separated, or empty): ").strip()
    carries = [c.strip().lower() for c in carries_str.split(",") if c.strip()]

    frame_id = f"frame_{len(labels) + 1:03d}"
    dest_filename = f"{frame_id}.jpg"
    dest_path = frames_dir / dest_filename

    shutil.copyfile(src_image, dest_path)

    new_label = {
        "id": frame_id,
        "filename": dest_filename,
        "description": desc,
        "expectedRole": role,
        "expectedIntent": intent,
        "expectedCarries": carries,
        "expectedSeverity": "calm" if role == "service_worker" else "attention",
    }

    labels.append(new_label)
    labels_file.write_text(json.dumps(labels, indent=2), encoding="utf-8")
    print(f"\nSuccessfully registered {dest_filename} into {labels_file}!")
    return 0


if __name__ == "__main__":
    sys.exit(label_frame_interactive())
