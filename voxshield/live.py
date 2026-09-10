from __future__ import annotations

import asyncio
import base64
import binascii
import hashlib
import hmac
import json
import struct
from dataclasses import dataclass, field
from urllib.parse import parse_qs
from xml.sax.saxutils import escape

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

from voxshield.schemas import AnalysisStatus


@dataclass
class CallBuffer:
    window_bytes: int
    max_bytes: int
    data: bytearray = field(default_factory=bytearray)
    last_chunk: int = -1
    sequence: int = 0

    def add(self, pcm: bytes, chunk: int) -> list[bytes]:
        if chunk <= self.last_chunk:
            return []
        self.last_chunk = chunk
        self.data.extend(pcm)
        if len(self.data) > self.max_bytes:
            del self.data[: len(self.data) - self.max_bytes]
        windows = []
        while len(self.data) >= self.window_bytes:
            windows.append(bytes(self.data[: self.window_bytes]))
            del self.data[: self.window_bytes]
        return windows


def decode_twilio_media(payload: str) -> bytes:
    try:
        mulaw = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("invalid base64 media payload") from exc
    samples = []
    for encoded in mulaw:
        value = ~encoded & 0xFF
        magnitude = ((value & 0x0F) << 3) + 0x84
        magnitude <<= (value & 0x70) >> 4
        sample = 0x84 - magnitude if value & 0x80 else magnitude - 0x84
        sample = max(-32768, min(32767, sample))
        samples.extend((sample, sample))  # Twilio 8 kHz to detector/transcriber 16 kHz PCM.
    return struct.pack(f"<{len(samples)}h", *samples)


async def analyze_window(app, session_id: str, pcm: bytes, sequence: int) -> None:
    manager = app.state.manager
    authenticity, transcription = await asyncio.gather(
        app.state.authenticity.analyze(pcm, sequence),
        app.state.transcription.transcribe(pcm, sequence),
    )
    manager.ingest_authenticity(session_id, authenticity)
    conversation = transcription
    if transcription.status == AnalysisStatus.READY and transcription.transcript:
        conversation = await app.state.scam.analyze(transcription.transcript, sequence)
    manager.ingest_conversation(session_id, conversation)


def live_router(config) -> APIRouter:
    router = APIRouter()

    @router.post("/api/v1/twilio/voice")
    async def incoming(request: Request) -> Response:
        if not config.public_base_url or not config.twilio_auth_token:
            raise HTTPException(503, "Twilio transport is not configured")
        form = parse_qs((await request.body()).decode("utf-8", errors="strict"))
        signed = config.public_base_url.rstrip("/") + "/api/v1/twilio/voice"
        signed += "".join(key + value for key in sorted(form) for value in sorted(form[key]))
        expected = base64.b64encode(
            hmac.new(config.twilio_auth_token.encode(), signed.encode(), hashlib.sha1).digest()
        ).decode()
        if not hmac.compare_digest(request.headers.get("X-Twilio-Signature", ""), expected):
            raise HTTPException(403, "Invalid Twilio signature")
        call_id = form.get("CallSid", [""])[0]
        if not call_id or len(call_id) > 64:
            raise HTTPException(400, "Missing or invalid CallSid")
        snapshot = await request.app.state.manager.create()
        request.app.state.manager.bind_call(snapshot.session_id, call_id)
        base = config.public_base_url.rstrip("/")
        ws_base = "wss" + base[5:] if base.startswith("https") else "ws" + base[4:]
        stream_url = escape(f"{ws_base}/api/v1/twilio/media/{snapshot.session_id}")
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?><Response><Start>'
            f'<Stream url="{stream_url}" track="inbound_track"/>'
            "</Start><Say>VoxShield monitoring is active.</Say></Response>"
        )
        return Response(xml, media_type="application/xml")

    @router.websocket("/api/v1/twilio/media/{session_id}")
    async def media(websocket: WebSocket, session_id: str) -> None:
        manager = websocket.app.state.manager
        try:
            manager.get(session_id)
        except KeyError:
            await websocket.close(code=1008)
            return
        await websocket.accept()
        buffer = CallBuffer(
            int(config.twilio_window_seconds * 16000 * 2),
            int(config.twilio_max_buffer_seconds * 16000 * 2),
        )
        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    message = json.loads(raw)
                except json.JSONDecodeError:
                    await websocket.close(code=1003)
                    return
                event = message.get("event")
                if event == "connected":
                    manager.emit_transport(session_id, "transport_connected", {})
                elif event == "start":
                    start = message.get("start", {})
                    manager.emit_transport(
                        session_id,
                        "media_stream_started",
                        {"stream_id": start.get("streamSid"), "format": start.get("mediaFormat")},
                    )
                elif event == "media":
                    media_data = message.get("media", {})
                    try:
                        chunk = int(media_data.get("chunk", -1))
                        pcm = decode_twilio_media(media_data.get("payload", ""))
                    except (TypeError, ValueError):
                        manager.emit_transport(
                            session_id, "media_rejected", {"reason": "invalid_media"}
                        )
                        continue
                    for window in buffer.add(pcm, chunk):
                        buffer.sequence += 1
                        manager.emit_transport(
                            session_id,
                            "audio_window_ready",
                            {
                                "sequence": buffer.sequence,
                                "duration_seconds": config.twilio_window_seconds,
                            },
                        )
                        await analyze_window(websocket.app, session_id, window, buffer.sequence)
                elif event == "stop":
                    manager.emit_transport(session_id, "media_stream_stopped", {})
                    break
        except WebSocketDisconnect:
            manager.emit_transport(session_id, "transport_disconnected", {})

    return router
