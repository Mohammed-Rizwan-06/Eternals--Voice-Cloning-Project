# VoxShield — AI / Cloned Voice Detector Prototype

This is the **detector-role MVP** for the VoxShield SIH prototype.

## What it does
- Accepts a WAV/FLAC audio clip through a small web UI.
- Converts audio to mono 16 kHz float32.
- Runs the official AASIST anti-spoofing model.
- Returns a transparent result:
  - `HUMAN LIKELY`
  - `POSSIBLE AI-CLONED VOICE`
  - `INSUFFICIENT SPEECH`
  - `DETECTOR UNAVAILABLE`
- Provides rolling-window style analysis in the API so the same detector can later consume Twilio/WebRTC chunks.

## Important
The architecture/decisions documents explicitly say the production path is controlled Twilio Media Streams, not arbitrary cellular-call interception. This upload UI is only a detector development/demo surface. Do not present it as the final telephony implementation.

## 1. Install

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

Install Git if needed, then:

```powershell
git clone https://github.com/clovaai/aasist.git model\aasist
```

The official repository contains the AASIST implementation and pretrained checkpoint.

## 2. Run

```powershell
uvicorn backend.main:app --reload --port 8000
```

Open:

http://127.0.0.1:8000

## 3. Test

Use a genuine human WAV and a synthetic/cloned WAV of at least ~4 seconds.

The API is:

`POST /api/detect`

form field:

`file=<audio file>`

Example response:

```json
{
  "status": "ok",
  "verdict": "POSSIBLE AI-CLONED VOICE",
  "human_probability": 0.18,
  "ai_probability": 0.82,
  "usable_speech_seconds": 4.04,
  "window_count": 1,
  "detector": "AASIST",
  "model_status": "ready"
}
```

## 4. Architecture integration

The detector is deliberately isolated behind:

`backend/detector.py`

Later, the team can call:

```python
result = detector.analyze_pcm_window(pcm_float32, 8000)
```

from the Twilio Media Streams branch after:

`base64 -> G.711 μ-law -> PCM -> bounded buffer -> VAD -> resample`

Do NOT put Twilio secrets in the frontend.
