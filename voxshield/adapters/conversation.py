from __future__ import annotations

import re
import wave
from io import BytesIO

from voxshield.schemas import AnalysisStatus, ConversationResult, ScamSignal, Severity
from voxshield.time import utc_now

RULES = (
    ("otp_request", Severity.CRITICAL, r"\b(?:otp|one[ -]time password|verification code)\b"),
    ("payment_request", Severity.HIGH, r"\b(?:pay|payment|transfer|send money|upi|wire funds?)\b"),
    ("password_request", Severity.CRITICAL, r"\b(?:password|passcode|cvv)\b"),
    ("pin_request", Severity.CRITICAL, r"\b(?:pin|personal identification number)\b"),
    (
        "fake_kyc",
        Severity.HIGH,
        r"\b(?:kyc|know your customer)\b.*\b(?:expire|block|suspend|update)\w*\b",
    ),
    (
        "bank_impersonation",
        Severity.HIGH,
        r"\b(?:calling|speaking) from (?:the )?(?:bank|rbi|reserve bank)\b",
    ),
    (
        "family_impersonation",
        Severity.HIGH,
        r"\b(?:your (?:son|daughter|child)|family member)\b.*"
        r"\b(?:accident|arrest|hospital|emergency)\b",
    ),
    (
        "threat",
        Severity.HIGH,
        r"\b(?:arrest|police|legal action|account (?:will be )?(?:blocked|frozen))\b",
    ),
    ("urgency", Severity.MEDIUM, r"\b(?:urgent|immediately|right now|act now)\b"),
)


class RuleBasedScamIntelligence:
    available = True

    async def analyze(self, transcript: str, sequence: int) -> ConversationResult:
        now = utc_now()
        signals = [
            ScamSignal(
                type=kind,
                severity=severity,
                evidence=f"Matched {kind.replace('_', ' ')} language.",
                timestamp=now,
                source="deterministic_phrase_rules",
            )
            for kind, severity, pattern in RULES
            if re.search(pattern, transcript, re.IGNORECASE)
        ]
        return ConversationResult(
            status=AnalysisStatus.READY,
            transcript=transcript,
            is_final=True,
            signals=signals,
            timestamp=now,
            sequence=sequence,
        )


class FasterWhisperTranscriptionAdapter:
    def __init__(self, model_name: str | None = None, model_factory=None):
        self._model = None
        if not model_name and model_factory is None:
            return
        try:
            if model_factory is None:
                from faster_whisper import WhisperModel

                model_factory = WhisperModel
            self._model = model_factory(model_name)
        except Exception:
            self._model = None

    @property
    def available(self) -> bool:
        return self._model is not None

    async def transcribe(self, audio: bytes, sequence: int) -> ConversationResult:
        if not self._model:
            return ConversationResult(
                status=AnalysisStatus.UNAVAILABLE, timestamp=utc_now(), sequence=sequence
            )
        try:
            wav = BytesIO()
            with wave.open(wav, "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(16000)
                output.writeframes(audio)
            wav.seek(0)
            segments, info = self._model.transcribe(wav, vad_filter=True)
            transcript = " ".join(segment.text.strip() for segment in segments).strip()
            return ConversationResult(
                status=AnalysisStatus.READY,
                transcript=transcript or None,
                is_final=True,
                language=getattr(info, "language", None),
                timestamp=utc_now(),
                sequence=sequence,
            )
        except Exception:
            return ConversationResult(
                status=AnalysisStatus.ERROR, timestamp=utc_now(), sequence=sequence
            )
