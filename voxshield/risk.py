from dataclasses import dataclass

from voxshield.schemas import (
    AnalysisStatus,
    AuthenticityResult,
    CallerInformation,
    ConversationResult,
    Reputation,
    RiskLevel,
    RiskResult,
    Severity,
)
from voxshield.time import utc_now


@dataclass(frozen=True)
class RiskPolicy:
    strong_ai: float = 0.80
    uncertain_ai: float = 0.40


SENSITIVE_SIGNAL_TYPES = {
    "otp_request",
    "pin_request",
    "password_request",
    "cvv_request",
    "payment_request",
    "bank_transfer_request",
    "remote_access_request",
}


class RiskEngine:
    def __init__(self, policy: RiskPolicy | None = None) -> None:
        self.policy = policy or RiskPolicy()

    def evaluate(
        self,
        caller: CallerInformation,
        authenticity: AuthenticityResult,
        conversation: ConversationResult,
        sequence: int,
    ) -> RiskResult:
        provenance = {caller.is_demo, authenticity.is_demo, conversation.is_demo}
        if len(provenance) != 1:
            raise ValueError("normal and demo data cannot be mixed")

        caller_risk = self._caller_risk(caller.reputation)
        ai_score = (
            authenticity.rolling_ai_probability
            if authenticity.rolling_ai_probability is not None
            else authenticity.ai_probability
        )
        authenticity_risk = self._authenticity_risk(authenticity.status, ai_score)
        conversation_risk = self._conversation_risk(conversation)

        critical_signals = [
            signal for signal in conversation.signals if signal.severity == Severity.CRITICAL
        ]
        high_signals = [
            signal
            for signal in conversation.signals
            if signal.severity in (Severity.HIGH, Severity.CRITICAL)
        ]
        sensitive_signal = next(
            (
                signal
                for signal in conversation.signals
                if signal.type in SENSITIVE_SIGNAL_TYPES
                and signal.severity in (Severity.HIGH, Severity.CRITICAL)
            ),
            None,
        )

        if (
            authenticity.status != AnalysisStatus.READY
            and conversation.status != AnalysisStatus.READY
            and caller.reputation == Reputation.UNAVAILABLE
        ):
            level = RiskLevel.UNAVAILABLE
            rules = ["RISK-ALL-UNAVAILABLE"]
            reasons = ["Caller, authenticity, and conversation assessment are unavailable."]
        elif (
            ai_score is not None
            and ai_score >= self.policy.strong_ai
            and sensitive_signal is not None
        ):
            level = RiskLevel.CRITICAL
            rules = ["RISK-CRITICAL-AI-SENSITIVE"]
            reasons = [
                f"Strong AI/cloned-voice evidence ({ai_score:.0%}) combined with "
                f"{sensitive_signal.type}: {sensitive_signal.evidence}"
            ]
        elif len(critical_signals) >= 2:
            level = RiskLevel.CRITICAL
            rules = ["RISK-CRITICAL-MULTI-SCAM"]
            reasons = [
                "Multiple critical scam indicators: "
                + ", ".join(signal.type for signal in critical_signals)
            ]
        elif critical_signals or len(high_signals) >= 2:
            level = RiskLevel.HIGH
            rules = ["RISK-HIGH-SCAM"]
            reasons = [
                "Strong conversation risk: " + ", ".join(signal.type for signal in high_signals)
            ]
        elif ai_score is not None and ai_score >= self.policy.strong_ai:
            level = RiskLevel.HIGH
            rules = ["RISK-HIGH-AI"]
            reasons = [
                f"Strong AI/cloned-voice evidence ({ai_score:.0%}); independently verify "
                "the caller."
            ]
        elif caller.reputation == Reputation.REPORTED:
            level = RiskLevel.HIGH
            rules = ["RISK-HIGH-REPORTED"]
            reasons = ["Caller reputation is reported."]
        elif (
            caller.reputation in (Reputation.UNKNOWN, Reputation.UNAVAILABLE)
            or authenticity_risk in (RiskLevel.MEDIUM, RiskLevel.UNAVAILABLE)
            or conversation_risk in (RiskLevel.MEDIUM, RiskLevel.UNAVAILABLE)
        ):
            level = RiskLevel.MEDIUM
            rules = ["RISK-MEDIUM-CAUTION"]
            reasons = [
                "Independent verification is recommended because one or more inputs are "
                "unknown, uncertain, or unavailable."
            ]
        else:
            level = RiskLevel.LOW
            rules = ["RISK-LOW-NO-CONCERN"]
            reasons = [
                "Available evidence shows likely human speech with no meaningful scam or "
                "caller-reputation concern."
            ]

        actions = {
            RiskLevel.LOW: "Continue monitoring.",
            RiskLevel.MEDIUM: "Use an independent trusted channel to verify the caller.",
            RiskLevel.HIGH: (
                "Do not share sensitive information; end the call and contact the person or "
                "institution using an official number."
            ),
            RiskLevel.CRITICAL: (
                "Do not transfer money or share credentials. Confirm ending the managed call "
                "and create a local prototype report."
            ),
            RiskLevel.UNAVAILABLE: (
                "Automated assessment unavailable; do not share sensitive information and "
                "verify independently."
            ),
        }
        return RiskResult(
            level=level,
            caller_risk=caller_risk,
            authenticity_risk=authenticity_risk,
            conversation_risk=conversation_risk,
            reasons=reasons,
            recommended_action=actions[level],
            triggered_rule_ids=rules,
            input_status={
                "caller": caller.reputation,
                "authenticity": authenticity.status,
                "conversation": conversation.status,
            },
            timestamp=utc_now(),
            sequence=sequence,
            is_demo=caller.is_demo,
        )

    def _authenticity_risk(self, status: AnalysisStatus, ai_score: float | None) -> RiskLevel:
        if status != AnalysisStatus.READY:
            return RiskLevel.UNAVAILABLE
        if ai_score is not None and ai_score >= self.policy.strong_ai:
            return RiskLevel.HIGH
        if ai_score is not None and ai_score >= self.policy.uncertain_ai:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    @staticmethod
    def _caller_risk(reputation: Reputation) -> RiskLevel:
        return {
            Reputation.TRUSTED: RiskLevel.LOW,
            Reputation.KNOWN: RiskLevel.LOW,
            Reputation.UNKNOWN: RiskLevel.MEDIUM,
            Reputation.REPORTED: RiskLevel.HIGH,
            Reputation.UNAVAILABLE: RiskLevel.UNAVAILABLE,
        }[reputation]

    @staticmethod
    def _conversation_risk(conversation: ConversationResult) -> RiskLevel:
        if conversation.status != AnalysisStatus.READY:
            return RiskLevel.UNAVAILABLE
        critical_count = sum(
            signal.severity == Severity.CRITICAL for signal in conversation.signals
        )
        high_count = sum(
            signal.severity in (Severity.HIGH, Severity.CRITICAL) for signal in conversation.signals
        )
        has_moderate = any(signal.severity == Severity.MEDIUM for signal in conversation.signals)
        if critical_count >= 2:
            return RiskLevel.CRITICAL
        if critical_count or high_count >= 2:
            return RiskLevel.HIGH
        if high_count or has_moderate:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
