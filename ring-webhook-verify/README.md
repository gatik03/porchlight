# ring-webhook-verify

Lightweight, zero-dependency HMAC-SHA256 signature verification for the Ring Partner API.

Published as part of the **Open Source Mini-Challenge** in the Amazon Developer Hackathon 2026.

## Installation

Not yet published to PyPI or npm. Install from source:

### Python
```bash
pip install ./python
```

### TypeScript / Node.js
```bash
cd typescript && npm install && npm run build && npm pack
npm install ./ring-webhook-verify-0.1.0.tgz   # from your project
```

Once published, these will become `pip install ring-webhook-verify` and `npm install ring-webhook-verify`.

## Quick Start

### Python (AWS Lambda)
```python
from ring_webhook_verify import verify_ring_signature

def lambda_handler(event, context):
    raw_body = event["body"].encode("utf-8")
    signature = event["headers"].get("X-Signature")
    secret = "your-hmac-secret-from-ring-portal"

    if not verify_ring_signature(raw_body, signature, secret):
        return {"statusCode": 401, "body": "Invalid signature"}

    return {"statusCode": 200, "body": "OK"}
```

### TypeScript (Express / Next.js)
```typescript
import { verifyRingSignature } from "ring-webhook-verify";

export function handleWebhook(rawBody: Buffer, signature: string, secret: string) {
  const isValid = verifyRingSignature(rawBody, signature, secret);
  if (!isValid) {
    throw new Error("Unauthorized");
  }
}
```

## License
MIT
