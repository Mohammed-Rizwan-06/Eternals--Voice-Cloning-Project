import base64
import hashlib
import hmac

import pytest
from fastapi.testclient import TestClient

from voxshield.adapters.authenticity import AASISTAuthenticityDetector
from voxshield.adapters.conversation import RuleBasedScamIntelligence
from voxshield.config import Settings
from voxshield.live import CallBuffer, decode_twilio_media
from voxshield.main import create_app


class FakeAASIST:
    def __init__(self, output):
        self.output = output

    def predict_pcm16(self, audio):
        return self.output


@pytest.mark.asyncio
async def test_phrase_rules_detect_otp_and_payment():
    result = await RuleBasedScamIntelligence().analyze(
        "Tell me your OTP and transfer the payment immediately", 1
    )
    assert {signal.type for signal in result.signals} >= {
        "otp_request",
        "payment_request",
        "urgency",
    }


@pytest.mark.asyncio
async def test_aasist_insufficient_speech_and_missing_model():
    detector = AASISTAuthenticityDetector()
    assert (await detector.analyze(b"\0" * 320, 1)).status == "insufficient_speech"
    loud = (1000).to_bytes(2, "little", signed=True) * 32000
    assert (await detector.analyze(loud, 2)).status == "unavailable"


@pytest.mark.asyncio
async def test_aasist_label_mapping_and_invalid_probabilities():
    loud = (1000).to_bytes(2, "little", signed=True) * 32000
    valid = await AASISTAuthenticityDetector(model=FakeAASIST([0.8, 0.2])).analyze(loud, 1)
    assert valid.ai_probability == pytest.approx(0.8)
    assert valid.human_probability == pytest.approx(0.2)
    invalid = await AASISTAuthenticityDetector(model=FakeAASIST([1.2, -0.2])).analyze(loud, 1)
    assert invalid.status == "error"
    assert invalid.ai_probability is None


def test_mulaw_decode_and_bounded_windows():
    payload = base64.b64encode(b"\xff" * 160).decode()
    pcm = decode_twilio_media(payload)
    assert len(pcm) == 640
    buffer = CallBuffer(window_bytes=1280, max_bytes=1920)
    assert buffer.add(pcm, 1) == []
    assert len(buffer.add(pcm, 2)) == 1
    assert buffer.add(pcm, 2) == []


def test_twilio_webhook_and_representative_websocket_events():
    token = "test-token"
    app = create_app(
        Settings(
            public_base_url="https://example.test", twilio_auth_token=token, twilio_window_seconds=1
        )
    )
    with TestClient(app) as client:
        signed = "https://example.test/api/v1/twilio/voiceCallSidCA123"
        signature = base64.b64encode(
            hmac.new(token.encode(), signed.encode(), hashlib.sha1).digest()
        ).decode()
        response = client.post(
            "/api/v1/twilio/voice",
            content="CallSid=CA123",
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "X-Twilio-Signature": signature,
            },
        )
        assert response.status_code == 200
        assert "wss://example.test/api/v1/twilio/media/" in response.text
        session_id = next(iter(app.state.manager.records))
        payload = base64.b64encode(b"\xff" * 8000).decode()
        with client.websocket_connect(f"/api/v1/twilio/media/{session_id}") as websocket:
            websocket.send_json({"event": "connected"})
            websocket.send_json(
                {
                    "event": "start",
                    "start": {
                        "streamSid": "MZ1",
                        "callSid": "CA123",
                        "tracks": ["inbound"],
                        "mediaFormat": {"encoding": "audio/x-mulaw", "sampleRate": 8000},
                    },
                }
            )
            websocket.send_json(
                {
                    "event": "media",
                    "media": {
                        "chunk": "1",
                        "timestamp": "0",
                        "track": "inbound",
                        "payload": payload,
                    },
                }
            )
            websocket.send_json({"event": "stop", "stop": {"accountSid": "AC1"}})
        types = [event.event_type for event in app.state.manager.records[session_id].events]
        assert "audio_window_ready" in types
        assert "media_stream_stopped" in types


def test_twilio_webhook_requires_configuration(normal_client):
    response = normal_client.post("/api/v1/twilio/voice", content="CallSid=CA123")
    assert response.status_code == 503
