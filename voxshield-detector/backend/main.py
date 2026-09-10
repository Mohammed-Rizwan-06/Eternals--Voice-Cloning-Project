import numpy as np
from pathlib import Path
import shutil
import tempfile

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from .stream_detector import StreamingDetector
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from . import detector

BASE = Path(__file__).resolve().parents[1]
FRONTEND = BASE / "frontend"

app = FastAPI(title="VoxShield AI Voice Detector", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")

@app.get("/api/health")
def health():
    return {
        "service": "VoxShield detector",
        "detector": "AASIST",
        "model_loaded": MODEL is not None,
        "model_error": MODEL_ERROR,
    }

@app.post("/api/detect")
async def detect(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".wav", ".flac"}:
        return {
            "status": "error",
            "verdict": "DETECTOR UNAVAILABLE",
            "error": "MVP currently accepts WAV or FLAC. Convert browser recordings to WAV before testing."
        }

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp_path = Path(tmp.name)
    tmp.close()

    try:
        with tmp_path.open("wb") as out:
            shutil.copyfileobj(file.file, out)
        return detector.analyze_file(str(tmp_path))
    finally:
        tmp_path.unlink(missing_ok=True)
@app.websocket("/ws/detect")
async def websocket_detect(websocket: WebSocket):

    await websocket.accept()

    stream = StreamingDetector()

    try:

        while True:

            data = await websocket.receive_bytes()

            # Browser sends PCM16 audio
            pcm = np.frombuffer(
                data,
                dtype=np.int16
            )

            # Convert PCM16 → float32 [-1, 1]
            audio = (
                pcm.astype(np.float32) / 32768.0
            )

            stream.add_audio(audio)
            result = stream.analyze()

            if result is not None:
                await websocket.send_json(result)
            

    except WebSocketDisconnect:

        print("VoxShield streaming client disconnected.")