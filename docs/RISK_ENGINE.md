# Deterministic prototype risk engine

Thresholds are centralized in `RiskPolicy` and are assumptions, not calibrated accuracy claims.

- `RISK-ALL-UNAVAILABLE`: caller unavailable plus both analysis branches without evidence → Unavailable.
- `RISK-CRITICAL-AI-SENSITIVE`: rolling/current AI ≥ 0.80 and a sensitive critical request (OTP, PIN, password, CVV, payment, transfer, remote access) → Critical.
- `RISK-CRITICAL-MULTI-SCAM`: at least two critical scam signals → Critical even for human voice.
- `RISK-HIGH-SCAM`: any critical signal or at least two high-or-worse signals → High.
- `RISK-HIGH-AI`: AI evidence ≥ 0.80 → High authenticity concern, with no financial-fraud claim unless scam evidence exists.
- `RISK-MEDIUM-*`: reported/unknown caller, uncertain AI evidence (≥ 0.40), one moderate warning, or partial unavailability → Medium.
- Otherwise sufficient likely-human/no-scam/no-reputation concern → Low.

Component risks remain separate in output. Reasons are generated only from supplied evidence; evidence strings are sanitized and bounded. Recommended actions range from continued monitoring to independent verification, ending via user confirmation, official callback, and local prototype reporting.

