# VoxShield

**Trust the voice. Verify the call.**

VoxShield is Team Eternals' SIH26104 prototype foundation for explainable near-real-time protection against voice-cloning impersonation and financial-scam calls.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m uvicorn voxshield.main:app --host 127.0.0.1 --port 8000
```

Set `VOXSHIELD_DEMO_MODE=true` deliberately for deterministic fixture sessions. In normal mode, missing provider adapters remain unavailable.

## Implemented in Bootstrap Y0

Typed contracts, adapter protocols, unavailable and deterministic fixture adapters, deterministic risk fusion, bounded in-memory sessions/SSE, REST commands, and tests.

## Not implemented yet

React frontend, Twilio/PSTN, WebRTC, AASIST or other authenticity inference, Whisper/ASR, production scam/caller services, authentication for internal ingestion, persistent reporting, deployment, or any teammate module. This is a hackathon integration foundation, not production readiness.

See [PROJECT_BRIEF.md](PROJECT_BRIEF.md), [ARCHITECTURE.md](ARCHITECTURE.md), and [docs/API_CONTRACT.md](docs/API_CONTRACT.md).

