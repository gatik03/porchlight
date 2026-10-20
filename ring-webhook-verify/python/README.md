# ring-webhook-verify

HMAC-SHA256 signature verification for Ring Partner API webhooks (hex or base64 digests, optional `sha256=` prefix). Zero dependencies.

## Install

Not yet published to PyPI. Install from source:

```bash
pip install ./ring-webhook-verify/python
```

## Usage

```python
from ring_webhook_verify import verify_ring_signature

ok = verify_ring_signature(raw_body_bytes, headers.get("X-Signature"), secret)
```

Pass the raw, unparsed request body. Comparison is constant-time.
