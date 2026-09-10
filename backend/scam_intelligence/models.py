"""
VoxShield - Scam Intelligence Data Models
Module: backend.scam_intelligence.models
Owner: Keerthi
Problem Statement #26104
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import datetime


class ScamCategory(str, Enum):
    """Taxonomy of scam vectors targeting voice channels."""
    CXO_IMPERSONATION = "cxo_impersonation"         # Executive voice clone, confidential wire transfer bypass
    DIGITAL_ARREST = "digital_arrest"               # Fake CBI/Police/Customs narcotics extortion
    UPI_BANKING_FRAUD = "upi_banking_fraud"         # KYC expiry, SIM block, OTP/UPI PIN theft
    REMOTE_ACCESS_COERCION = "remote_access"        # AnyDesk, TeamViewer screen takeover
    SAFE_ACCOUNT_SCAM = "safe_account_scam"         # RBI / Government verification account transfer
    CREDENTIAL_HARVESTING = "credential_harvesting" # Netbanking password, CVV, Card numbers
    LOTTERY_PRIZE_FRAUD = "lottery_prize_fraud"     # KBC/Lottery clearance fee
    BENIGN = "benign"                               # Normal non-fraudulent conversation


class ThreatLevel(str, Enum):
    """Categorical threat rating for risk fusion (Yash) and frontend (Mohit)."""
    BENIGN = "BENIGN"       # 0.0 - 0.2
    LOW = "LOW"             # 0.2 - 0.4
    MEDIUM = "MEDIUM"       # 0.4 - 0.65
    HIGH = "HIGH"           # 0.65 - 0.85
    CRITICAL = "CRITICAL"   # 0.85 - 1.0


class UrgencyLevel(str, Enum):
    """Psychological urgency intensity."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


class ActionType(str, Enum):
    """Prescriptive action for victim or frontline personnel."""
    NO_ACTION = "NO_ACTION"
    WARN_USER = "WARN_USER"
    BLOCK_TRANSACTION = "BLOCK_TRANSACTION"
    TERMINATE_CALL = "TERMINATE_CALL"
    ESCALATE_SUPERVISOR = "ESCALATE_SUPERVISOR"
    TRIGGER_CALLBACK_VERIFICATION = "TRIGGER_CALLBACK_VERIFICATION"


@dataclass
class ExtractedFinancialEntities:
    """Entities harvested during real-time speech inspection."""
    amounts_inr: List[str] = field(default_factory=list)
    amounts_usd: List[str] = field(default_factory=list)
    upi_ids: List[str] = field(default_factory=list)
    bank_names: List[str] = field(default_factory=list)
    account_numbers: List[str] = field(default_factory=list)
    ifsc_codes: List[str] = field(default_factory=list)
    otps: List[str] = field(default_factory=list)
    remote_tools: List[str] = field(default_factory=list)
    claimed_authorities: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "amounts_inr": self.amounts_inr,
            "amounts_usd": self.amounts_usd,
            "upi_ids": self.upi_ids,
            "bank_names": self.bank_names,
            "account_numbers": self.account_numbers,
            "ifsc_codes": self.ifsc_codes,
            "otps": [f"***{otp[-2:]}" if len(otp) > 2 else "***" for otp in self.otps],  # Masked for privacy
            "remote_tools": self.remote_tools,
            "claimed_authorities": self.claimed_authorities,
        }


@dataclass
class MatchedPattern:
    """Specific rule or regex pattern triggered in conversation."""
    category: ScamCategory
    pattern_id: str
    matched_text: str
    weight: float
    description: str


@dataclass
class PsychologicalIndicators:
    """Social engineering behavioral indicators."""
    urgency_score: float = 0.0             # Time limit intimidation
    authority_intimidation_score: float = 0.0 # Police, CBI, CEO power posture
    secrecy_isolation_score: float = 0.0   # Demands to not speak with family/bank
    coercion_pressure_score: float = 0.0   # Threat of arrest, account termination

    def to_dict(self) -> dict:
        return {
            "urgency_score": round(self.urgency_score, 2),
            "authority_intimidation_score": round(self.authority_intimidation_score, 2),
            "secrecy_isolation_score": round(self.secrecy_isolation_score, 2),
            "coercion_pressure_score": round(self.coercion_pressure_score, 2),
        }


@dataclass
class ScamAnalysisResult:
    """Comprehensive output emitted from Keerthi's Scam Intelligence engine."""
    session_id: str
    overall_scam_score: float               # 0.0 to 1.0
    threat_level: ThreatLevel
    primary_scam_type: ScamCategory
    confidence: float                       # 0.0 to 1.0
    is_imminent_threat: bool
    matched_patterns: List[MatchedPattern] = field(default_factory=list)
    extracted_entities: ExtractedFinancialEntities = field(default_factory=ExtractedFinancialEntities)
    psychological_indicators: PsychologicalIndicators = field(default_factory=PsychologicalIndicators)
    explanation: str = ""
    recommended_action: str = ""
    action_type: ActionType = ActionType.NO_ACTION
    created_at_iso: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "overall_scam_score": round(self.overall_scam_score, 3),
            "threat_level": self.threat_level.value,
            "primary_scam_type": self.primary_scam_type.value,
            "confidence": round(self.confidence, 3),
            "is_imminent_threat": self.is_imminent_threat,
            "matched_patterns": [
                {
                    "category": p.category.value,
                    "pattern_id": p.pattern_id,
                    "matched_text": p.matched_text,
                    "weight": p.weight,
                    "description": p.description,
                }
                for p in self.matched_patterns
            ],
            "extracted_entities": self.extracted_entities.to_dict(),
            "psychological_indicators": self.psychological_indicators.to_dict(),
            "explanation": self.explanation,
            "recommended_action": self.recommended_action,
            "action_type": self.action_type.value,
            "created_at_iso": self.created_at_iso,
        }
