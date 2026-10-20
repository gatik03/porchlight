#!/usr/bin/env python3
"""Generate synthetic doorstep benchmark test frames matching fixtures/frames/labels.json."""

from __future__ import annotations

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def generate_frames():
    root = Path(__file__).resolve().parents[2]
    labels_file = root / "fixtures" / "frames" / "labels.json"
    output_dir = root / "fixtures" / "frames"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not labels_file.is_file():
        print(f"Labels file not found: {labels_file}")
        return

    labels = json.loads(labels_file.read_text(encoding="utf-8"))
    print(f"Generating {len(labels)} benchmark test frames in {output_dir}...")

    # Palette
    role_colors = {
        "courier": (30, 60, 110),
        "delivery_food": (110, 50, 30),
        "service_worker": (30, 90, 60),
        "neighbor_or_friend": (60, 40, 90),
        "solicitor": (80, 80, 40),
        "animal": (40, 70, 70),
        "vehicle_only": (50, 50, 60),
        "child": (90, 60, 80),
    }

    for item in labels:
        filename = item["filename"]
        out_path = output_dir / filename
        role = item.get("expectedRole", "unknown")
        intent = item.get("expectedIntent", "unknown")
        desc = item.get("description", "")
        carries = ", ".join(item.get("expectedCarries", [])) or "None"

        # 640x360 16:9 frame
        bg_color = role_colors.get(role, (35, 35, 40))
        img = Image.new("RGB", (640, 360), color=bg_color)
        draw = ImageDraw.Draw(img)

        # Draw porch simulation geometry
        draw.rectangle([(0, 260), (640, 360)], fill=(20, 20, 25)) # Porch floor
        draw.rectangle([(220, 60), (420, 260)], fill=(45, 45, 55)) # Front Door
        draw.rectangle([(380, 150), (395, 165)], fill=(200, 180, 100)) # Door handle

        # Watermark
        draw.text((20, 20), "RING DEVELOPER SIMULATION", fill=(180, 180, 180))
        draw.text((20, 40), "PORCHLIGHT BENCHMARK FIXTURE", fill=(130, 130, 140))

        # Test case metadata box
        draw.rectangle([(40, 275), (600, 345)], fill=(10, 10, 15))
        draw.text((50, 285), f"ROLE: {role.upper()}  |  INTENT: {intent.upper()}", fill=(255, 255, 255))
        draw.text((50, 305), f"SCENE: {desc}", fill=(200, 200, 200))
        draw.text((50, 325), f"CARRIES: {carries}", fill=(100, 200, 255))

        img.save(out_path, "JPEG", quality=90)
        print(f"Generated {filename}")

    print("All 10 benchmark frames successfully generated!")


if __name__ == "__main__":
    generate_frames()
