# Porchlight: Developer Experience Friction Log

> **Purpose:** Real-time log of undocumented quirks, SDK gaps, tooling limitations, and developer friction encountered during building. Used directly for DevRel product feedback scoring in the Amazon Developer Hackathon 2026.

---

## F-001: Ring Partner API Lacks Native Two-Way Audio Talk Endpoint
- **Task:** Enable residents to speak directly to doorstep visitors from the responsive dashboard.
- **Steps:** Searched Ring Partner API and WebRTC WHEP documentation for two-way audio talk endpoints.
- **Expected:** A standard WebRTC ingest endpoint or two-way audio session endpoint matching consumer Ring app capabilities.
- **Actual:** The current Partner API exposes WHEP for one-way downlink (video + audio), but no uplink audio endpoint is available for third-party developer integrations.
- **Severity:** High (Missing capability)
- **Workaround:** Implemented high-contrast Amazon Transcribe live speech-to-text captions so residents can at least read visitors. Documented two-way talk as our #1 Critical Feature Request in `docs/FEATURE_REQUESTS.md`.
- **Suggestion:** Expose WHIP (WebRTC HTTP Ingestion Protocol) or an authenticated audio send endpoint to enable two-way talk for accessibility and intercom applications.

---

## F-002: Webhook Payloads Do Not Embed Event-Scoped Media Snapshots
- **Task:** Retrieve immediate doorstep image upon button press event.
- **Steps:** Evaluated Ring webhook payload schemas for `button_press` and `motion_detected`.
- **Expected:** A signed S3 URL or base64 thumbnail of the event frame embedded directly inside the webhook payload.
- **Actual:** Webhook delivers metadata only (`event_id`, `device_id`, timestamps). The backend must make a secondary asynchronous call to the Image Snapshots API or download a video clip to obtain imagery.
- **Severity:** Medium
- **Workaround:** Architected multi-tier `frames.py` strategy (Snapshot API -> Media Clip -> Dashboard captured frame -> graceful text fallback).
- **Suggestion:** Include an optional low-resolution thumbnail or temporary signed S3 image URL directly inside webhook payloads to reduce round-trip latency for computer vision applications.

---

## F-003: Amazon Transcribe Not Available on the New AWS Experience Free Plan
- **Task:** Stream live speech-to-text captions from the doorbell audio via Amazon Transcribe Streaming.
- **Steps:** Built the presign Lambda and browser event-stream client, then checked the plan's supported-services list when the service could not be used.
- **Expected:** Transcribe usable (within free-tier limits) on a new AWS account.
- **Actual:** The free plan's supported-services list does not include Amazon Transcribe; it needs the paid plan.
- **Severity:** Medium (Blocks a core feature on the free plan)
- **Workaround:** Stayed on the free plan. The dashboard falls back to clearly labelled scripted "Demo captions" with a visible reason; the Transcribe code stays in place and would work on a paid plan.
- **Suggestion:** Flag plan-restricted services in the console and IaC docs before build time, or allow a small Transcribe free-tier allowance on the free plan.
