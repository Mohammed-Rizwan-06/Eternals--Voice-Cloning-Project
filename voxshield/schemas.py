from __future__ import annotations

import math
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator


def validate_utc_timestamp(value: datetime) -> datetime:
    """Reject naive and non-UTC timestamps at every external schema boundary."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    if value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must use UTC")
    return value


UtcTimestamp = Annotated[datetime, AfterValidator(validate_utc_timestamp)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class Reputation(StrEnum):
    TRUSTED = "trusted"
    KNOWN = "known"
    UNKNOWN = "unknown"
    REPORTED = "reported"
    UNAVAILABLE = "unavailable"


class ServiceState(StrEnum):
    READY = "ready"
    LOADING = "loading"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class AnalysisStatus(StrEnum):
    LOADING = "loading"
    READY = "ready"
    INSUFFICIENT_SPEECH = "insufficient_speech"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNAVAILABLE = "unavailable"


class CallState(StrEnum):
    CREATED = "created"
    INCOMING = "incoming"
    ACTIVE = "active"
    ENDING = "ending"
    ENDED = "ended"


class ProtectionState(StrEnum):
    DISABLED = "disabled"
    ACTIVE = "active"
    STOPPED = "stopped"


class CallerInformation(StrictModel):
    display_name: str = Field(min_length=1, max_length=100)
    masked_phone_number: str = Field(min_length=3, max_length=32, pattern=r"^[+*xX\-() .0-9]+$")
    region: str = Field(default="Unavailable", max_length=80)
    category: str = Field(default="Unknown", max_length=80)
    reputation: Reputation = Reputation.UNAVAILABLE
    report_count: int | None = Field(default=None, ge=0)
    data_source: str = Field(default="unavailable", max_length=100)
    is_demo: bool = False


class ServiceStatus(StrictModel):
    telephony: ServiceState = ServiceState.UNAVAILABLE
    authenticity_detector: ServiceState = ServiceState.UNAVAILABLE
    transcription: ServiceState = ServiceState.UNAVAILABLE
    scam_intelligence: ServiceState = ServiceState.UNAVAILABLE
    risk_engine: ServiceState = ServiceState.READY
    event_stream: ServiceState = ServiceState.READY


class AuthenticityResult(StrictModel):
    status: AnalysisStatus
    human_probability: float | None = None
    ai_probability: float | None = None
    rolling_ai_probability: float | None = None
    valid_windows: int = Field(default=0, ge=0)
    usable_speech_seconds: float = Field(default=0, ge=0)
    inference_ms: float | None = Field(default=None, ge=0)
    detector_name: str | None = Field(default=None, max_length=120)
    warnings: list[str] = Field(default_factory=list, max_length=20)
    timestamp: UtcTimestamp
    sequence: int = Field(ge=0)
    is_demo: bool = False

    @model_validator(mode="after")
    def validate_prediction(self) -> AuthenticityResult:
        probabilities = (
            self.human_probability,
            self.ai_probability,
            self.rolling_ai_probability,
        )
        if any(
            value is not None and (not math.isfinite(value) or not 0 <= value <= 1)
            for value in probabilities
        ):
            raise ValueError("probabilities must be finite and within [0,1]")
        if (self.human_probability is None) != (self.ai_probability is None):
            raise ValueError("human and AI probabilities must be supplied together")
        if (
            self.human_probability is not None
            and abs(self.human_probability + self.ai_probability - 1) > 1e-6
        ):
            raise ValueError("human and AI probabilities must sum to 1")
        if self.status != AnalysisStatus.READY and any(
            value is not None for value in probabilities
        ):
            raise ValueError("non-ready states cannot contain predictions")
        return self


class ScamSignal(StrictModel):
    type: str = Field(min_length=1, max_length=80)
    severity: Severity
    evidence: str = Field(min_length=1, max_length=240)
    timestamp: UtcTimestamp
    source: str = Field(min_length=1, max_length=80)


class ConversationResult(StrictModel):
    status: AnalysisStatus
    transcript: str | None = Field(default=None, max_length=2000)
    is_final: bool = False
    language: str | None = Field(default=None, max_length=32)
    signals: list[ScamSignal] = Field(default_factory=list, max_length=50)
    transcription_ms: float | None = Field(default=None, ge=0)
    timestamp: UtcTimestamp
    sequence: int = Field(ge=0)
    is_demo: bool = False

    @model_validator(mode="after")
    def validate_evidence(self) -> ConversationResult:
        if self.status != AnalysisStatus.READY and (self.transcript or self.signals):
            raise ValueError("non-ready conversation states cannot contain transcript or signals")
        return self


class RiskResult(StrictModel):
    level: RiskLevel
    caller_risk: RiskLevel
    authenticity_risk: RiskLevel
    conversation_risk: RiskLevel
    reasons: list[str] = Field(default_factory=list, max_length=30)
    recommended_action: str = Field(min_length=1, max_length=500)
    triggered_rule_ids: list[str] = Field(default_factory=list, max_length=20)
    input_status: dict[str, str]
    timestamp: UtcTimestamp
    sequence: int = Field(ge=0)
    is_demo: bool = False


class SessionSnapshot(StrictModel):
    session_id: str
    call_id: str | None = None
    call_state: CallState
    protection_state: ProtectionState
    caller: CallerInformation
    authenticity: AuthenticityResult
    conversation: ConversationResult
    risk: RiskResult
    service_status: ServiceStatus
    created_at: UtcTimestamp
    updated_at: UtcTimestamp
    is_demo: bool = False

    @model_validator(mode="after")
    def validate_provenance(self) -> SessionSnapshot:
        derived_values = (self.caller, self.authenticity, self.conversation, self.risk)
        if any(value.is_demo != self.is_demo for value in derived_values):
            raise ValueError("normal and demo data cannot be mixed")
        return self


class SSEEvent(StrictModel):
    session_id: str
    sequence: int = Field(ge=1)
    event_type: str
    timestamp: UtcTimestamp
    payload: dict[str, Any]
    is_demo: bool


class SessionCreateRequest(StrictModel):
    scenario: str | None = None


class HealthResponse(StrictModel):
    status: str
    demo_mode: bool
    is_demo: bool
    services: ServiceStatus
