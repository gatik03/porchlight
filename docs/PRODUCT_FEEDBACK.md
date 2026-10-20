# Porchlight: Developer Product Feedback

> **Submission Requirement:** Detailed feedback per tool used during building for the Amazon Developer Relations teams.

---

## 1. Ring Developer Portal & Event Simulator
- **Used For:** Simulating doorbell button presses and motion events without physical Ring hardware.
- **What Worked Well:** The ability to simulate events (`button_press`, `motion_detected`, `person`) and immediately test webhook delivery without requiring physical devices or subscriptions was a massive accelerator. The portal UI is clean and reactive.
- **What Needs Work:** 
  1. The simulator does not currently emit an event-scoped image or snapshot payload; developers must make secondary asynchronous calls to media endpoints.
  2. The webhook history in the portal could benefit from showing raw response bodies and HTTP status codes when delivery fails.
- **Onboarding Experience:** Smooth and accessible. Setting up the application and configuring the staging webhook URL took less than 15 minutes.
- **Would Build With It Again?** Yes, absolutely. It makes third-party Ring integrations viable for any developer without upfront hardware investment.

---

## 2. Ring Partner API & Webhook Protocol
- **Used For:** Ingesting doorstep events, OAuth 2.0 account linking, and media fetching.
- **What Worked Well:** Standardized HMAC-SHA256 signature verification in `X-Signature` header provides robust cryptographic authentication. The JSON:API payload structure is comprehensive.
- **What Needs Work:** 
  1. Lack of a two-way audio talk-back endpoint over WebRTC limits developer innovation for remote intercoms and accessibility aids.
  2. The 5-second webhook timeout is strict; developers must implement asynchronous message queueing (like SQS) to prevent retry loops.
- **Onboarding Experience:** Clear API documentation, though discovering exact snapshot endpoint paths required experimentation.
- **Would Build With It Again?** Yes.

---

## 3. Amazon Bedrock (Converse API)
- **Used For:** Multimodal vision reasoning on doorbell frames (answering *"Who is here and what do they want?"* in <= 20 words) and text narration for caretaker digests.
- **What Worked Well:** The Converse API (`boto3.client('bedrock-runtime').converse`) provides a beautifully unified interface across different foundation models (Amazon Nova and Anthropic Claude). Response latency was consistently between 2.0s and 3.5s.
- **What Needs Work:** Strict adherence to negative constraints (e.g., "never include names or facial descriptions") requires explicit few-shot system prompts and client-side JSON schema validation.
- **Onboarding Experience:** Enabling model access in the AWS console was instantaneous for Nova models.
- **Would Build With It Again?** 100% yes; Bedrock is our default choice for generative and multimodal AI.

---

## 4. Amazon Transcribe Streaming (WebSocket)
- **Used For:** Real-time speech-to-text live captions of doorstep visitor audio streamed from Ring WHEP WebRTC connection.
- **What Worked Well:** Low latency (< 300ms) from audio chunk arrival to partial transcript event. High transcription accuracy even on casual conversational speech.
- **What Needs Work:** SigV4 presigned WebSocket URL generation for browser clients requires manual query-string formatting. An official browser SDK utility for direct PCM streaming would save developer time.
- **Onboarding Experience:** Good once audio sampling rates (16,000 Hz PCM) were properly matched in the browser's Web Audio API.
- **Would Build With It Again?** Yes, essential for any accessible audio experience.

---

## 5. React Native for Vega & Amazon Devices Builder Tools (ADBT) MCP
- **Used For:** Building the full-screen 10-foot Fire TV card display with flashing borders and D-pad navigation.
- **What Worked Well:** Lean, native television rendering without bloated web wrappers. Excellent remote D-pad focus management via `hasTVPreferredFocus`.
- **What Needs Work:** Emulating TV displays locally requires the Vega Virtual Device (VVD); clearer CLI documentation for command-line installs would be helpful.
- **Onboarding Experience:** Very fast when reusing established 10-foot theme patterns.
- **Would Build With It Again?** Yes, it is the premier path for native Fire TV apps.

---

## 6. AWS SAM (Serverless Application Model) & Lambda ARM64
- **What Worked Well:** Declarative serverless infrastructure combining API Gateway, Lambda, SQS, DynamoDB, S3, and EventBridge into a single readable `template.yaml`. ARM64 Graviton execution reduced cost and achieved cold starts under 250ms.
- **What Needs Work:** Testing complex SQS event source mappings locally still requires mock harnesses (like `moto`).
- **Would Build With It Again?** Definitively; SAM remains the most reliable infrastructure-as-code for serverless projects on AWS.
