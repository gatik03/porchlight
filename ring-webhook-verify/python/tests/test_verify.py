import sys
from pathlib import Path

SRC_DIR = str(Path(__file__).resolve().parents[1] / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from ring_webhook_verify import compute_ring_signature, verify_ring_signature


def test_package_verification():
    secret = "ring-webhook-shared-secret"
    payload = b'{"data":{"type":"events","attributes":{"event_type":"button_press"}}}'

    sig_hex = compute_ring_signature(payload, secret, encoding="hex")
    assert verify_ring_signature(payload, sig_hex, secret) is True

    sig_b64 = compute_ring_signature(payload, secret, encoding="base64")
    assert verify_ring_signature(payload, sig_b64, secret) is True

    assert verify_ring_signature(payload, "invalid_signature", secret) is False
