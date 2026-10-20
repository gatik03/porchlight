# Porchlight: Ring Developer Platform Feature Requests

> **Context:** Constructive feedback submitted as part of the Amazon Developer Hackathon 2026 Ring Track.

---

## 1. Feature Request (CRITICAL): WebRTC Two-Way Audio Talk-Back Endpoint
- **Severity / Priority:** Critical
- **Problem Statement:** The current Ring Partner API exposes WHEP (WebRTC HTTP Egress Protocol) for one-way downlink of video and audio streams. However, there is no supported endpoint or protocol (such as WHIP or bidirectional WebRTC) allowing third-party applications to stream resident audio *back* to the doorbell speaker.
- **Why This Matters:** For Deaf residents, elderly individuals with mobility impairments, and smart intercom integrations, speaking through the doorbell is the primary interaction after an alert occurs. Today, developers must force residents to open the native Ring consumer mobile app, breaking the unified assistive experience.
- **Proposed Solution:** Expose a WHIP (WebRTC HTTP Ingestion Protocol) endpoint or an authenticated WebSocket audio uplink allowing 16 kHz or 48 kHz Opus/PCM audio streaming to specific doorbell devices.

---

## 2. Feature Request (IMPORTANT): Event-Scoped Image Snapshot in Webhook Payloads
- **Severity / Priority:** Important
- **Problem Statement:** When a `button_press` or `motion_detected` webhook arrives, it contains event metadata (`event_id`, `device_id`, timestamps), but no image data. The backend must initiate a secondary asynchronous request to fetch an image snapshot or download a video clip.
- **Why This Matters:** This adds 1.5 to 3.0 seconds of latency to computer vision and assistive notification pipelines. Every second of delay impacts the resident's ability to answer before a courier walks away.
- **Proposed Solution:** Include an optional temporary signed S3 URL or low-resolution base64 thumbnail (e.g., 480x270 JPEG) directly within the webhook payload's `attributes` block.

---

## 3. Feature Request (USABILITY): Audio Channel in Developer Simulator WHEP Stream
- **Severity / Priority:** Medium
- **Problem Statement:** The Ring Developer Portal Event Simulator provides video test feeds over WHEP, but simulated streams currently lack an active audio track.
- **Why This Matters:** Developers testing speech-to-text, captioning, or audio event detection must manually mock audio inputs or rely on uploaded video files during testing.
- **Proposed Solution:** Include a synthetic speech loop or tone track on the simulated WHEP stream to facilitate audio and captioning pipeline verification.
