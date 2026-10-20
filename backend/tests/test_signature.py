"""Unit tests for HMAC signature verification."""

from common.signature import compute_webhook_signature, verify_webhook_signature


def test_signature_hex_valid():
    key = "test-secret-key"
    body = b'{"hello": "world"}'
    sig = compute_webhook_signature(body, key, encoding="hex")

    assert verify_webhook_signature(body, sig, key) is True


def test_signature_base64_valid():
    key = "test-secret-key"
    body = b'{"hello": "world"}'
    sig = compute_webhook_signature(body, key, encoding="base64")

    assert verify_webhook_signature(body, sig, key) is True


def test_signature_with_sha256_prefix():
    key = "test-secret-key"
    body = b'{"hello": "world"}'
    sig = "sha256=" + compute_webhook_signature(body, key, encoding="hex")

    assert verify_webhook_signature(body, sig, key) is True


def test_signature_with_v1_prefix():
    key = "test-secret-key"
    body = b'{"hello": "world"}'
    sig = "v1=" + compute_webhook_signature(body, key, encoding="hex")

    assert verify_webhook_signature(body, sig, key) is True


def test_signature_tampered_body():
    key = "test-secret-key"
    body = b'{"hello": "world"}'
    sig = compute_webhook_signature(body, key, encoding="hex")
    tampered_body = b'{"hello": "tampered"}'

    assert verify_webhook_signature(tampered_body, sig, key) is False


def test_signature_wrong_key():
    body = b'{"hello": "world"}'
    sig = compute_webhook_signature(body, "key1", encoding="hex")

    assert verify_webhook_signature(body, sig, "key2") is False


def test_signature_empty_or_none():
    assert verify_webhook_signature(b"", "sig", "key") is False
    assert verify_webhook_signature(b"data", None, "key") is False
    assert verify_webhook_signature(b"data", "", "key") is False
    assert verify_webhook_signature(b"data", "sig", "") is False
