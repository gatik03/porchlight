import * as crypto from "crypto";

/**
 * Verify incoming Ring webhook signature using HMAC-SHA256.
 *
 * @param rawBody - Raw Buffer or string of the request body before JSON parsing.
 * @param signatureHeader - X-Signature header value.
 * @param secretKey - Shared secret key.
 * @returns boolean indicating if the signature is valid.
 */
export function verifyRingSignature(
  rawBody: Buffer | string,
  signatureHeader: string | undefined | null,
  secretKey: string
): boolean {
  if (!signatureHeader || !rawBody || !secretKey) {
    return false;
  }

  let cleanHeader = signatureHeader.trim();
  if (cleanHeader.includes("=") && !cleanHeader.endsWith("=")) {
    const parts = cleanHeader.split("=", 2);
    if (parts.length === 2 && parts[0].length <= 8) {
      cleanHeader = parts[1];
    }
  }

  const bodyBuffer = Buffer.isBuffer(rawBody) ? rawBody : Buffer.from(rawBody, "utf-8");
  const hmac = crypto.createHmac("sha256", secretKey).update(bodyBuffer);

  const hexDigest = hmac.digest("hex");
  const b64Digest = crypto.createHmac("sha256", secretKey).update(bodyBuffer).digest("base64");

  try {
    const cleanBuf = Buffer.from(cleanHeader.toLowerCase(), "utf-8");
    const hexBuf = Buffer.from(hexDigest.toLowerCase(), "utf-8");
    if (cleanBuf.length === hexBuf.length && crypto.timingSafeEqual(cleanBuf, hexBuf)) {
      return true;
    }

    const b64Buf = Buffer.from(cleanHeader, "utf-8");
    const expectedB64Buf = Buffer.from(b64Digest, "utf-8");
    if (b64Buf.length === expectedB64Buf.length && crypto.timingSafeEqual(b64Buf, expectedB64Buf)) {
      return true;
    }
  } catch {
    return false;
  }

  return false;
}
