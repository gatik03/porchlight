# Porchlight: Privacy & Data Minimization Architecture

> **Guiding Principle:** Assistive AI must respect human dignity and privacy. Porchlight completely rejects biometric surveillance in favor of contextual assistance.

---

## 1. Zero Facial Recognition & Biometric Stance

Porchlight explicitly **forbids facial recognition, person re-identification, and biometric feature extraction**:
- **No Face Embeddings:** Images captured by the doorbell camera are never processed for facial geometry, landmark detection, or facial verification.
- **No Demographic Profiling:** The vision system is instructed and programmatically constrained to **never** estimate age, gender, or racial/ethnic identity.
- **Role & Action Focus:** Computer vision models are prompted strictly to describe *roles* and *actions* (e.g., *"A courier in a high-visibility vest is holding a parcel."* or *"A service worker with a toolbox is at the door."*).

---

## 2. Schedule-Based Matching (No Personal Names Stored in AI)

- Household expected visitor schedules ("Nurse Priya, Tue/Thu 10:00") are stored securely in DynamoDB and are **never** passed to the vision AI model.
- The model receives only generalized role tags (e.g., `Expected roles today: service_worker, courier`).
- Matching is performed by deterministic application rules (`common/matcher.py`) based on arrival time, day of the week, and recognized role.
- Schema validators (`common/validate.py`) actively reject any generated output that accidentally contains personal visitor names.

---

## 3. Data Retention & Automatic Purging

Porchlight enforces strict automated data lifecycle policies across all storage tiers:

| Data Type | Storage Location | Retention / Expiration | Mechanism |
|---|---|---|---|
| **Doorstep Frames** | Amazon S3 | **7 days** | S3 native lifecycle expiration |
| **Presigned Frame URLs** | API Gateway / S3 | **1 hour** | SigV4 time-limited expiration |
| **Event Deduplication Tokens** | Amazon DynamoDB | **72 hours** | DynamoDB native TTL |
| **Event History & Cards** | Amazon DynamoDB | **30 days** | DynamoDB native TTL |
| **Household Settings** | Amazon DynamoDB | Indefinite (User-controlled) | Deletable via PUT `/api/settings` |

---

## 4. Encryption & Security

- **At Rest:** All DynamoDB items, S3 objects, and SSM parameters are encrypted at rest using AWS KMS managed keys.
- **In Transit:** All communication between Ring, API Gateway, AWS Lambda, Amazon Bedrock, Transcribe, and client displays is encrypted with TLS 1.3 / HTTPS / WSS.
- **Zero Secrets in Code:** Credentials and signing keys reside exclusively in AWS Systems Manager Parameter Store (`SecureString`).
