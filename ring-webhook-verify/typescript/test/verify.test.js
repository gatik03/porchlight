const test = require("node:test");
const assert = require("node:assert");
const crypto = require("node:crypto");
const { verifyRingSignature } = require("../dist/index.js");

const secret = "ring-webhook-shared-secret";
const payload = Buffer.from('{"data":{"type":"events","attributes":{"event_type":"button_press"}}}');
const hmac = () => crypto.createHmac("sha256", secret).update(payload);

test("accepts correct hex, prefixed hex and base64 signatures", () => {
  assert.strictEqual(verifyRingSignature(payload, hmac().digest("hex"), secret), true);
  assert.strictEqual(verifyRingSignature(payload, "sha256=" + hmac().digest("hex"), secret), true);
  assert.strictEqual(verifyRingSignature(payload, hmac().digest("base64"), secret), true);
});

test("rejects tampered body, bad signature and wrong secret", () => {
  const sig = hmac().digest("hex");
  assert.strictEqual(verifyRingSignature(Buffer.from(payload + " "), sig, secret), false);
  assert.strictEqual(verifyRingSignature(payload, "invalid_signature", secret), false);
  assert.strictEqual(verifyRingSignature(payload, sig, "other-secret"), false);
});
