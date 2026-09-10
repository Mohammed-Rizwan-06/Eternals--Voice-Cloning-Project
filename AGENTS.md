# VoxShield repository rules

- This repository is the SIH 2026 VoxShield integration foundation. Preserve truthful capability labels.
- Normal mode must use unavailable adapters until genuine integrations are installed; never silently fall back to Demo Mode.
- Demo outputs must be deterministic and carry `is_demo: true` through every derived result and event.
- Keep caller, authenticity, conversation, and fused risks distinct. Human speech never means a call is safe; AI-like speech alone never proves financial fraud.
- Never fabricate predictions, progress, availability, accuracy, action confirmation, or teammate integration.
- Never execute untrusted pickle/joblib artifacts. Do not log raw phone numbers, audio, secrets, or full sensitive transcripts.
- Validate external input, use timezone-aware UTC timestamps, enforce monotonic sequences, and bound buffers/queues.
- Keep adapters replaceable and schemas stable. Add tests for behavior changes.
- Do not implement teammate-owned Twilio, WebRTC, AASIST, ASR, scam-model, caller-provider, or frontend work without explicit approval.
- Do not commit `.env` or push a remote unless explicitly requested.

