# API and event contract

Canonical executable definitions live in `voxshield/schemas.py`.

## Schemas

- `CallerInformation`: display name, masked number, region/category, reputation, optional report count, source, demo flag.
- `ServiceStatus`: telephony, authenticity detector, transcription, scam intelligence, risk engine, event stream.
- `AuthenticityResult`: status, optional probability pair/rolling value, speech/window measures, detector/latency/warnings, timestamp, monotonic sequence, demo flag.
- `ScamSignal`: type, severity, redacted evidence, timestamp, source.
- `ConversationResult`: status, ephemeral transcript, final/language/signals/latency, timestamp, sequence, demo flag.
- `RiskResult`: fused and component levels, exact reasons/action/rule IDs/input status, timestamp, sequence, demo flag.
- `SessionSnapshot`: identifiers/states plus caller, analysis, risk, services, timestamps, demo flag.

Finite probabilities are in `[0,1]`; when both exist they must sum to 1 within `1e-6`. Failure/unavailable/insufficient states cannot contain predictions. Demo provenance must be consistent. Session ingestion rejects duplicate or stale branch sequences.

## REST and SSE

`GET /api/v1/health`; `POST /api/v1/sessions`; `GET /api/v1/sessions/{id}`; `GET /api/v1/sessions/{id}/events`; and POST commands `/enable`, `/verify`, `/stop-protection`, `/end`, `/report`. Health returns both `demo_mode` and the universal `is_demo` provenance marker.

Commands return structured snapshots. SSE envelopes contain `session_id`, global monotonic `sequence`, `event_type`, aware UTC `timestamp`, relevant `payload`, and `is_demo`. Session retention, history, and subscriber queues are bounded. Slow subscribers may miss old events and must refresh the snapshot.

Event vocabulary: `session_created`, `incoming_call`, `receiver_ringing`, `call_answered`, `protection_enabled`, `service_status`, `audio_window_received`, `insufficient_speech`, `authenticity_updated`, `transcript_updated`, `scam_signal_detected`, `conversation_updated`, `risk_updated`, `verification_requested`, `protection_stopped`, `call_ending`, `call_ended`, `session_summary`, `transport_error`, `analysis_error`.

Internal adapter ingestion is intentionally not exposed as unauthenticated HTTP in Y0.
