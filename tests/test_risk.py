from voxshield.risk import RiskEngine
from voxshield.schemas import (
    AnalysisStatus,
    AuthenticityResult,
    CallerInformation,
    ConversationResult,
    Reputation,
    RiskLevel,
    ScamSignal,
    Severity,
)
from voxshield.time import utc_now

NOW = utc_now()


def caller(rep=Reputation.TRUSTED):
    return CallerInformation(
        display_name="Test", masked_phone_number="***", reputation=rep, data_source="test"
    )


def auth(ai=0.05, status=AnalysisStatus.READY):
    kw = (
        {}
        if status != AnalysisStatus.READY
        else dict(
            human_probability=1 - ai,
            ai_probability=ai,
            rolling_ai_probability=ai,
            valid_windows=2,
            usable_speech_seconds=6,
        )
    )
    return AuthenticityResult(status=status, timestamp=NOW, sequence=1, **kw)


def signal(kind, severity, evidence):
    return ScamSignal(type=kind, severity=severity, evidence=evidence, timestamp=NOW, source="test")


def convo(signals=(), status=AnalysisStatus.READY):
    return ConversationResult(status=status, signals=list(signals), timestamp=NOW, sequence=1)


def risk(c=None, a=None, v=None):
    return RiskEngine().evaluate(c or caller(), a or auth(), v or convo(), 1)


def test_detector_unavailable_can_continue_with_conversation():
    result = risk(
        a=auth(status=AnalysisStatus.UNAVAILABLE),
        v=convo([signal("otp_request", Severity.CRITICAL, "OTP requested")]),
    )
    assert result.level == RiskLevel.HIGH and result.authenticity_risk == RiskLevel.UNAVAILABLE


def test_asr_unavailable_can_continue_with_authenticity():
    result = risk(a=auth(0.9), v=convo(status=AnalysisStatus.UNAVAILABLE))
    assert result.level == RiskLevel.HIGH and "financial" not in " ".join(result.reasons).lower()


def test_both_branches_and_caller_unavailable():
    result = risk(
        c=caller(Reputation.UNAVAILABLE),
        a=auth(status=AnalysisStatus.UNAVAILABLE),
        v=convo(status=AnalysisStatus.UNAVAILABLE),
    )
    assert result.level == RiskLevel.UNAVAILABLE


def test_human_scammer_is_high_or_critical():
    signals = [
        signal("otp_request", Severity.CRITICAL, "OTP requested"),
        signal("payment_request", Severity.CRITICAL, "Payment requested"),
    ]
    assert risk(a=auth(0.05), v=convo(signals)).level == RiskLevel.CRITICAL


def test_ai_without_scam_does_not_claim_financial_fraud():
    result = risk(a=auth(0.92))
    assert result.level == RiskLevel.HIGH
    assert "financial" not in " ".join(result.reasons).lower()


def test_ai_with_sensitive_request_is_critical_and_explained():
    result = risk(
        a=auth(0.92), v=convo([signal("otp_request", Severity.CRITICAL, "Caller requested an OTP")])
    )
    assert result.level == RiskLevel.CRITICAL
    assert result.triggered_rule_ids == ["RISK-CRITICAL-AI-SENSITIVE"]
    assert "Caller requested an OTP" in result.reasons[0]
