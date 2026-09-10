# Teammate adapter integration

Implement the protocol in `voxshield/adapters/protocols.py`; do not put provider logic in sessions or risk fusion.

1. Validate provider initialization and inputs; return contract status rather than fabricated values.
2. Convert outputs to canonical schemas with aware UTC timestamps, monotonic per-branch sequences, latency, version/source, warnings, and truthful `is_demo=False`.
3. Keep raw audio outside snapshots/events and avoid sensitive logging. Bound any transport/window buffers.
4. Add unit tests for failures, insufficient speech, label mapping, stale/duplicate data, and cleanup.
5. Wire the adapter explicitly in application composition after review. Do not replace failures with fixture data.

Pranita supplies `AuthenticityDetector`; Keerti supplies transcription and scam adapters; Rizwan supplies telephony; a future provider supplies caller reputation. Mohit's frontend consumes the documented REST/SSE surface. Contract changes require Yash-led coordination.

