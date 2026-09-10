# Architecture

## Preferred path

1. An informed caller reaches a VoxShield-controlled Twilio number.
2. A webhook creates an ephemeral session and the receiver explicitly enables protection.
3. Twilio Media Streams sends only inbound/caller G.711 μ-law audio to a protected WebSocket.
4. Bounded decoded speech windows independently feed authenticity detection and ASR/scam intelligence.
5. Risk fusion combines fresh caller, authenticity, conversation, and availability evidence.
6. Ordered bounded SSE events update the dashboard; REST handles user commands.
7. On call end, raw buffers are discarded and only a minimal summary may remain.

## Fallback order

1. Twilio PSTN + Media Streams (preferred).
2. Two-party browser WebRTC, analysing the remote participant stream.
3. Local microphone monitoring, visibly labelled **Simulated Call**.

Upload is developer/evaluation utility only. Fallback activation requires an explicit decision. Current Y0 implements contracts, session/risk orchestration, REST/SSE, unavailable adapters, and deterministic fixtures—not transport or ML.

