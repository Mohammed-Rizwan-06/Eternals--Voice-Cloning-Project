from datetime import datetime, timedelta

from voxshield.schemas import (
    AnalysisStatus,
    AuthenticityResult,
    CallerInformation,
    ConversationResult,
    Reputation,
    ScamSignal,
    Severity,
)

SCENARIOS = (
    "safe_human",
    "unknown_human",
    "human_financial_scam",
    "ai_cloned_financial_scam",
)

DISPLAY_NAMES = {
    "safe_human": "Aarav (Demo)",
    "unknown_human": "Unknown Caller (Demo)",
    "human_financial_scam": "Bank Desk (Demo)",
    "ai_cloned_financial_scam": "Family Member (Demo)",
}

AI_PROBABILITIES = {
    "safe_human": 0.05,
    "unknown_human": 0.08,
    "human_financial_scam": 0.06,
    "ai_cloned_financial_scam": 0.94,
}


def fixture(
    scenario: str, base: datetime
) -> tuple[CallerInformation, AuthenticityResult, ConversationResult]:
    if scenario not in SCENARIOS:
        choices = ", ".join(SCENARIOS)
        raise ValueError(f"unknown scenario; choose one of {choices}")

    reputation = Reputation.TRUSTED if scenario == "safe_human" else Reputation.UNKNOWN
    caller = CallerInformation(
        display_name=DISPLAY_NAMES[scenario],
        masked_phone_number="+91 ******4321",
        region="Demo region",
        category="Demo fixture",
        reputation=reputation,
        data_source="deterministic_fixture",
        is_demo=True,
    )
    ai_probability = AI_PROBABILITIES[scenario]
    authenticity = AuthenticityResult(
        status=AnalysisStatus.READY,
        human_probability=1 - ai_probability,
        ai_probability=ai_probability,
        rolling_ai_probability=ai_probability,
        valid_windows=3,
        usable_speech_seconds=9,
        inference_ms=24,
        detector_name="deterministic-fixture",
        timestamp=base + timedelta(seconds=2),
        sequence=1,
        is_demo=True,
    )

    signal_values: list[tuple[str, Severity, str]] = []
    if scenario == "human_financial_scam":
        signal_values = [
            ("bank_impersonation", Severity.HIGH, "Claims to represent a bank."),
            ("urgency", Severity.HIGH, "Creates immediate urgency."),
            ("otp_request", Severity.CRITICAL, "Requests an OTP."),
        ]
    elif scenario == "ai_cloned_financial_scam":
        signal_values = [
            ("family_impersonation", Severity.HIGH, "Claims to be a family member."),
            ("urgency", Severity.HIGH, "Demands immediate action."),
            ("payment_request", Severity.CRITICAL, "Requests an urgent payment."),
            ("otp_request", Severity.CRITICAL, "Requests an OTP."),
        ]

    signals = [
        ScamSignal(
            type=signal_type,
            severity=severity,
            evidence=evidence,
            timestamp=base + timedelta(seconds=3 + index),
            source="deterministic_fixture",
        )
        for index, (signal_type, severity, evidence) in enumerate(signal_values)
    ]
    conversation = ConversationResult(
        status=AnalysisStatus.READY,
        transcript="[Deterministic demo transcript]" if signals else None,
        is_final=False,
        language="en",
        signals=signals,
        transcription_ms=31,
        timestamp=base + timedelta(seconds=4),
        sequence=1,
        is_demo=True,
    )
    return caller, authenticity, conversation
