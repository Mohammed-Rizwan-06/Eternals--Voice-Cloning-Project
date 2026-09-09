from dataclasses import dataclass, field

from voxshield.schemas import (
    AnalysisStatus,
    AuthenticityResult,
    CallerInformation,
    ConversationResult,
    Reputation,
)
from voxshield.time import utc_now


class UnavailableTelephonyAdapter:
    available = False

    async def end_call(self, call_id: str) -> bool:
        return False


class UnavailableAuthenticityDetector:
    available = False

    async def analyze(self, audio: bytes, sequence: int) -> AuthenticityResult:
        return AuthenticityResult(
            status=AnalysisStatus.UNAVAILABLE,
            timestamp=utc_now(),
            sequence=sequence,
            warnings=["Authenticity detector is not installed."],
        )


class UnavailableTranscriptionAdapter:
    available = False

    async def transcribe(self, audio: bytes, sequence: int) -> ConversationResult:
        return ConversationResult(
            status=AnalysisStatus.UNAVAILABLE,
            timestamp=utc_now(),
            sequence=sequence,
        )


class UnavailableScamIntelligenceAdapter:
    available = False

    async def analyze(self, transcript: str, sequence: int) -> ConversationResult:
        return ConversationResult(
            status=AnalysisStatus.UNAVAILABLE,
            timestamp=utc_now(),
            sequence=sequence,
        )


class UnavailableCallerReputationAdapter:
    available = False

    async def lookup(self, masked_number: str) -> CallerInformation:
        return CallerInformation(
            display_name="Unknown caller",
            masked_phone_number=masked_number,
            reputation=Reputation.UNAVAILABLE,
        )


@dataclass(frozen=True)
class UnavailableAdapters:
    telephony: UnavailableTelephonyAdapter = field(default_factory=UnavailableTelephonyAdapter)
    authenticity: UnavailableAuthenticityDetector = field(
        default_factory=UnavailableAuthenticityDetector
    )
    transcription: UnavailableTranscriptionAdapter = field(
        default_factory=UnavailableTranscriptionAdapter
    )
    scam: UnavailableScamIntelligenceAdapter = field(
        default_factory=UnavailableScamIntelligenceAdapter
    )
    caller: UnavailableCallerReputationAdapter = field(
        default_factory=UnavailableCallerReputationAdapter
    )
