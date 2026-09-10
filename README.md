# Eternals--Voice-Cloning-Project

## VoxShield

**Trust the voice. Verify the call.**

VoxShield is Team Eternals' SIH26104 prototype foundation for explainable near-real-time protection against voice-cloning impersonation and financial-scam calls.

## Run the backend

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m uvicorn voxshield.main:app --host 127.0.0.1 --port 8000
```

Set `VOXSHIELD_DEMO_MODE=true` deliberately for deterministic fixture sessions. In normal mode, missing provider adapters remain unavailable.

## Run the interactive Demo Mode frontend

Start the backend in explicit Demo Mode:

```powershell
$env:VOXSHIELD_DEMO_MODE="true"
.\.venv\Scripts\python.exe -m uvicorn voxshield.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173/`. The frontend reads `VITE_API_BASE_URL`, defaulting to `http://127.0.0.1:8000`. It requires the real health response to confirm explicit Demo Mode before creating deterministic sessions.

## Implemented

Bootstrap Y0 provides typed contracts, adapter protocols, unavailable and deterministic fixture adapters, deterministic risk fusion, bounded in-memory sessions/SSE, REST commands, and tests.

Phase Y1 adds a responsive React/Vite frontend for the four deterministic API scenarios, actual backend health state, SSE updates, and Verify, End, and Report command integration. All simulated values remain visibly labelled as Demo Mode.

## Not implemented yet

Twilio/PSTN, WebRTC, AASIST or other authenticity inference, Whisper/ASR, production scam/caller services, authentication for internal ingestion, persistent reporting destinations, deployment, or any teammate module. The frontend is a deterministic demo interface, not a live-call product or production readiness.

See [PROJECT_BRIEF.md](PROJECT_BRIEF.md), [ARCHITECTURE.md](ARCHITECTURE.md), and [docs/API_CONTRACT.md](docs/API_CONTRACT.md).
