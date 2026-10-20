#!/usr/bin/env python3
"""Tool to sign and POST a fixture webhook to a local or deployed Porchlight endpoint."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import requests

# Ensure common is on sys.path
SRC_DIR = str(Path(__file__).resolve().parents[2] / "backend" / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from common.signature import compute_webhook_signature


def replay(fixture_path: Path, target_url: str, hmac_key: str, encoding: str = "hex") -> int:
    """Read fixture, sign raw bytes, and post to target."""
    if not fixture_path.is_file():
        print(f"Error: Fixture file not found: {fixture_path}", file=sys.stderr)
        return 1

    raw_body = fixture_path.read_bytes()
    signature = compute_webhook_signature(raw_body, hmac_key, encoding=encoding)

    headers = {
        "Content-Type": "application/json",
        "X-Signature": signature,
        "User-Agent": "Ring-Event-Simulator/1.0",
    }

    print(f"Replaying {fixture_path.name} -> {target_url}")
    print(f"Signature (HMAC-SHA256 {encoding}): {signature[:16]}...")

    try:
        response = requests.post(target_url, data=raw_body, headers=headers, timeout=5)
        print(f"Response: HTTP {response.status_code}")
        print(response.text)
        return 0 if response.status_code == 200 else 1
    except Exception as e:
        print(f"Network error: {e}", file=sys.stderr)
        return 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay fixture webhook with valid HMAC signature")
    parser.add_argument("--fixture", required=True, help="Path to fixture JSON file")
    parser.add_argument("--target", required=True, help="Target webhook URL")
    parser.add_argument("--hmac-key", default="test-secret-hmac-key", help="HMAC secret key")
    parser.add_argument("--encoding", choices=["hex", "base64"], default="hex", help="Signature encoding")

    args = parser.parse_args()
    return replay(Path(args.fixture), args.target, args.hmac_key, args.encoding)


if __name__ == "__main__":
    sys.exit(main())
