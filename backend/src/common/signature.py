"""HMAC-SHA256 signature verification for Ring webhooks."""

from __future__ import annotations

import base64
import hmac
import hashlib
from typing import Union


def compute_webhook_signature(
    raw_body: bytes,
    key: Union[str, bytes],
    encoding: str = "hex"
) -> str:
    """Compute HMAC-SHA256 signature for a raw body.
    
    Args:
        raw_body: The unparsed byte sequence of the request body.
        key: The shared HMAC secret key.
        encoding: 'hex' (default) or 'base64'.
        
    Returns:
        The encoded signature string.
    """
    key_bytes = key.encode("utf-8") if isinstance(key, str) else key
    mac = hmac.new(key_bytes, raw_body, hashlib.sha256)
    if encoding == "base64":
        return base64.b64encode(mac.digest()).decode("ascii")
    return mac.hexdigest()


def verify_webhook_signature(
    raw_body: bytes,
    header: str | None,
    key: Union[str, bytes]
) -> bool:
    """Verify X-Signature header against raw body using HMAC-SHA256.
    
    Supports both hex and base64 encodings, and strips optional 'sha256=' or 'v1=' prefixes.
    Uses constant-time comparison to prevent timing attacks.
    
    Args:
        raw_body: Raw unparsed bytes of the incoming request body.
        header: The signature string from the X-Signature header.
        key: The shared secret key.
        
    Returns:
        True if the signature matches, False otherwise.
    """
    if not header or not raw_body or not key:
        return False

    header_clean = header.strip()
    # Strip optional prefix like 'sha256=' or 'v1='
    if "=" in header_clean and not header_clean.endswith("="):
        parts = header_clean.split("=", 1)
        if len(parts) == 2 and len(parts[0]) <= 8:
            header_clean = parts[1]

    key_bytes = key.encode("utf-8") if isinstance(key, str) else key
    expected_mac = hmac.new(key_bytes, raw_body, hashlib.sha256)

    expected_hex = expected_mac.hexdigest()
    expected_b64 = base64.b64encode(expected_mac.digest()).decode("ascii")

    # Constant-time comparison against both hex and base64 variants
    if hmac.compare_digest(header_clean.lower(), expected_hex.lower()):
        return True
    if hmac.compare_digest(header_clean, expected_b64):
        return True

    return False
