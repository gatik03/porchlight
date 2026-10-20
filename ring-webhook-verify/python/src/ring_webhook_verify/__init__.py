"""Ring Partner API Webhook Verification Helper."""

from __future__ import annotations

import base64
import hashlib
import hmac
from typing import Union

__version__ = "0.1.0"


def verify_ring_signature(
    raw_body: bytes,
    signature_header: str | None,
    secret_key: Union[str, bytes]
) -> bool:
    """Verify incoming Ring webhook X-Signature header using HMAC-SHA256.
    
    Supports both hex and base64 encoded digests, and handles optional prefixes
    such as 'sha256=' or 'v1='.
    
    Args:
        raw_body: Unparsed byte sequence of the HTTP request body.
        signature_header: Raw signature string from HTTP X-Signature header.
        secret_key: Shared webhook secret key configured in Ring Developer Portal.
        
    Returns:
        True if signature is valid, False otherwise.
    """
    if not signature_header or not raw_body or not secret_key:
        return False

    header_clean = signature_header.strip()
    if "=" in header_clean and not header_clean.endswith("="):
        parts = header_clean.split("=", 1)
        if len(parts) == 2 and len(parts[0]) <= 8:
            header_clean = parts[1]

    key_bytes = secret_key.encode("utf-8") if isinstance(secret_key, str) else secret_key
    expected_mac = hmac.new(key_bytes, raw_body, hashlib.sha256)

    expected_hex = expected_mac.hexdigest()
    expected_b64 = base64.b64encode(expected_mac.digest()).decode("ascii")

    if hmac.compare_digest(header_clean.lower(), expected_hex.lower()):
        return True
    if hmac.compare_digest(header_clean, expected_b64):
        return True

    return False


def compute_ring_signature(
    raw_body: bytes,
    secret_key: Union[str, bytes],
    encoding: str = "hex"
) -> str:
    """Compute HMAC-SHA256 signature for test fixtures and event replay."""
    key_bytes = secret_key.encode("utf-8") if isinstance(secret_key, str) else secret_key
    mac = hmac.new(key_bytes, raw_body, hashlib.sha256)
    if encoding == "base64":
        return base64.b64encode(mac.digest()).decode("ascii")
    return mac.hexdigest()
