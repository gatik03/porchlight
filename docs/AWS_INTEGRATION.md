# Porchlight: AWS Builder Mini-Challenge Integration Evidence

> **Project:** Porchlight  
> **Challenge:** AWS Builder Mini-Challenge (Amazon Developer Hackathon 2026)  
> **Infrastructure as Code:** `backend/template.yaml` (AWS SAM)  

---

## 1. Overview of AWS Services Used

Porchlight integrates **9 distinct AWS serverless and artificial intelligence services** into an event-driven architecture designed for high availability, sub-second ingestion, and low operational cost:

```
Ring Webhook ────────► API Gateway HTTP API
                            │
                            ▼
                    Webhook Lambda
                      │        │ (Dedupe)
                      │        ▼
                      │    DynamoDB (porchlight)
                      ▼
                   Amazon SQS (porchlight-events)
                      │
                      ▼
               Processor Lambda ───► Amazon Bedrock (Vision)
                 │          │
                 ▼          ▼
            Amazon S3    DynamoDB (CURRENT# & EVENT#)
                 ▲
                 │ (Presigned URL)
           Read API Lambda ◄─── Fire TV (Vega) & Next.js Dashboard
                 │
                 ▼
         Amazon Transcribe (Streaming WebSocket for Live Captions)
```

---

## 2. Service-by-Service Breakdown

### 2.1 Amazon Bedrock (Multimodal Vision & Text Generation)
- **What it does:**
  - *Vision:* Analyzes doorbell video frames via the Converse API (`amazon.nova-lite-v1:0` or `anthropic.claude-3-5-sonnet`) to describe who is at the door and their intent in <= 20 words without biometric facial recognition.
  - *Text:* Generates warm, objective daily caretaker narratives (<= 120 words) from rule-detected anomalies.
- **Template Reference:** `backend/template.yaml` lines 122–126 and 188–192 (`bedrock:InvokeModel`).
- **Implementation File:** `backend/src/common/vision.py` and `backend/src/common/digest.py`.
- **Evidence:** Tested with schema validation and automated repair retry in `backend/tests/test_vision_parsing.py`.

### 2.2 Amazon Transcribe (Streaming Speech-to-Text WebSocket)
- **What it does:** Streams real-time 16 kHz PCM audio extracted directly from the Ring WebRTC WHEP connection to generate live captions on the dashboard.
- **Template Reference:** `backend/template.yaml` lines 180–184 (`transcribe:StartStreamTranscriptionWebSocket`).
- **Implementation File:** `backend/src/handlers/transcribe_auth.py` and `dashboard/lib/transcribeClient.ts`.
- **Evidence:** Tested with presigned SigV4 URL generation and 16 kHz PCM AudioContext downsampling.
- **Plan limitation:** Live Transcribe requires an AWS paid plan. This deployment runs on the free plan, so the demo shows labelled scripted captions ("Demo captions"). The presign Lambda and event-stream client are implemented and would work on a paid plan.

### 2.3 Amazon DynamoDB (Single-Table Event Store & Deduplication)
- **What it does:** Houses all event deduplication tokens (`DEDUPE#`), active television cards (`CURRENT#`), 30-day event history (`EVENT#`), household settings (`SETTINGS#`), and daily digests (`DIGEST#`) with automatic TTL data eviction.
- **Template Reference:** `backend/template.yaml` lines 41–60 (`PorchlightTable`).
- **Implementation File:** `backend/src/common/store.py`.
- **Evidence:** 100% verified using `moto` in `backend/tests/test_store.py` (idempotent dedupe, atomic updates).

### 2.4 Amazon SQS (Decoupling & Dead Letter Queue)
- **What it does:** Decouples fast webhook acknowledgment (< 1.0s) from compute-intensive Bedrock vision inference (2.5–4.5s). Automatically retries failures up to 3 times before routing to `porchlight-events-dlq`.
- **Template Reference:** `backend/template.yaml` lines 79–94 (`PorchlightEventsQueue` and `PorchlightEventsDLQ`).
- **Implementation File:** `backend/src/handlers/webhook.py` and `backend/src/handlers/processor.py`.
- **Evidence:** Verified in `backend/tests/test_webhook_handler.py` and `backend/tests/test_processor.py`.

### 2.5 AWS Lambda (ARM64 / Graviton Serverless Handlers)
- **What it does:** 5 dedicated single-responsibility Python 3.12 handlers:
  1. `WebhookFunction`: Fast < 1s ingestion and HMAC verification.
  2. `ProcessorFunction`: SQS consumer with reserved concurrency = 3.
  3. `ReadApiFunction`: Long-polling card delivery and settings API.
  4. `TranscribeAuthFunction`: Presigned URL generator.
  5. `DigestJobFunction`: Scheduled nightly caretaker digest engine.
- **Template Reference:** `backend/template.yaml` lines 97–198.
- **Evidence:** Cold starts < 250ms on ARM64 Graviton architecture.

### 2.6 Amazon API Gateway (HTTP API v2)
- **What it does:** Serves as the public ingestion endpoint (`/ring/webhook`) and client API (`/api/*`) with native CORS configuration and low-latency payload routing.
- **Template Reference:** `backend/template.yaml` lines 23–38 (`PorchlightHttpApi`).
- **Implementation File:** Routes mapped in `template.yaml`.

### 2.7 Amazon S3 (Private Doorstep Frame Storage)
- **What it does:** Stores doorbell snapshots and extracted video frames with strict public access blocks. Automatically expires old frames after 7 days via lifecycle rules. Clients access frames using 1-hour presigned GET URLs.
- **Template Reference:** `backend/template.yaml` lines 63–76 (`PorchlightFramesBucket`).
- **Implementation File:** `backend/src/handlers/processor.py` (`_upload_frame_and_presign`).

### 2.8 Amazon EventBridge Scheduler (Nightly Cron)
- **What it does:** Triggers `DigestJobFunction` at `cron(30 23 * * ? *)` (23:30 nightly) to aggregate the day's events, detect anomalies, and generate the caregiver summary note.
- **Template Reference:** `backend/template.yaml` lines 193–198 (`NightlySchedule`).
- **Implementation File:** `backend/src/handlers/digest_job.py`.

### 2.9 AWS Systems Manager (SSM) Parameter Store
- **What it does:** Securely stores Ring client secrets, HMAC signing keys, and household passphrases as encrypted `SecureString` parameters. Eliminates credentials from source control.
- **Template Reference:** `backend/template.yaml` IAM policies (`SSMParameterReadPolicy`).
- **Implementation File:** `backend/src/common/config.py`.
