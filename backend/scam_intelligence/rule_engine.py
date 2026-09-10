"""
VoxShield - Deterministic Rule & Pattern Engine
Module: backend.scam_intelligence.rule_engine
Owner: Keerthi
Problem Statement #26104

Executes zero-latency regex matching, financial entity extraction,
and immediate critical trigger detection (<5ms execution budget).
"""

from typing import Dict, List, Tuple
from .models import (
    ExtractedFinancialEntities,
    MatchedPattern,
    ScamCategory,
    ThreatLevel,
)
from .patterns import ENTITY_REGEXES, SCAM_PATTERNS


class RuleEngine:
    """
    High-speed deterministic matcher for telephony transcript chunks.
    Extracts financial identifiers and flags immediate high-risk indicators.
    """

    def __init__(self):
        self.patterns = SCAM_PATTERNS
        self.entity_regexes = ENTITY_REGEXES

    def extract_entities(self, text: str) -> ExtractedFinancialEntities:
        """Extract all financial, authority, and tooling entities from dialogue."""
        entities = ExtractedFinancialEntities()

        # INR Amounts
        inr_matches = self.entity_regexes["inr_amount"].findall(text)
        entities.amounts_inr = [m.strip() for m in inr_matches]

        # USD Amounts
        usd_matches = self.entity_regexes["usd_amount"].findall(text)
        entities.amounts_usd = [m.strip() for m in usd_matches]

        # UPI IDs
        upi_matches = [m.group(0) for m in self.entity_regexes["upi_id"].finditer(text)]
        entities.upi_ids = list(set(upi_matches))

        # OTP codes
        otp_matches = []
        for match in self.entity_regexes["otp_code"].finditer(text):
            code = match.group(1) or match.group(2)
            if code:
                otp_matches.append(code)
        entities.otps = list(set(otp_matches))

        # Bank Names
        bank_matches = [m.group(0).upper() for m in self.entity_regexes["bank_name"].finditer(text)]
        entities.bank_names = list(set(bank_matches))

        # Remote Desktop Tools
        rmt_matches = [m.group(0).lower() for m in self.entity_regexes["remote_tools"].finditer(text)]
        entities.remote_tools = list(set(rmt_matches))

        # Claimed Authorities
        auth_matches = [m.group(0).upper() for m in self.entity_regexes["law_authorities"].finditer(text)]
        entities.claimed_authorities = list(set(auth_matches))

        # Account numbers
        acc_matches = [m.group(1) for m in self.entity_regexes["account_number"].finditer(text)]
        entities.account_numbers = list(set(acc_matches))

        return entities

    def evaluate(self, text: str) -> Tuple[List[MatchedPattern], Dict[ScamCategory, float], bool]:
        """
        Scans text across all scam categories.
        Returns:
            - matched_patterns: list of triggered rules
            - category_scores: raw accumulated weights per category
            - is_imminent_threat: bool flag if immediate critical trigger hit
        """
        matched_patterns: List[MatchedPattern] = []
        category_scores: Dict[ScamCategory, float] = {cat: 0.0 for cat in ScamCategory}
        is_imminent_threat = False

        for category, rules in self.patterns.items():
            for rule in rules:
                matches = rule["regex"].finditer(text)
                for match in matches:
                    matched_str = match.group(0)
                    weight = rule["weight"]

                    pattern = MatchedPattern(
                        category=category,
                        pattern_id=rule["id"],
                        matched_text=matched_str,
                        weight=weight,
                        description=rule["desc"],
                    )
                    matched_patterns.append(pattern)
                    category_scores[category] += weight

                    # Immediate high-danger conditions:
                    # Asking for OTP, UPI PIN, Remote Access, or Bypass Wire Transfer
                    if weight >= 0.85:
                        is_imminent_threat = True

        # Check multi-entity correlations (e.g., AnyDesk + OTP, or Authority + Money)
        extracted = self.extract_entities(text)
        if extracted.remote_tools and (extracted.otps or extracted.amounts_inr):
            is_imminent_threat = True
            category_scores[ScamCategory.REMOTE_ACCESS_COERCION] += 0.50

        if extracted.claimed_authorities and (extracted.amounts_inr or extracted.amounts_usd):
            category_scores[ScamCategory.DIGITAL_ARREST] += 0.40

        return matched_patterns, category_scores, is_imminent_threat
