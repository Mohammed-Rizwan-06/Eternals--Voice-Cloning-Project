"""
VoxShield - Heuristic & Psychological Coercion Engine
Module: backend.scam_intelligence.heuristic_engine
Owner: Keerthi
Problem Statement #26104

Calculates behavioral pressure indices:
1. Urgency Index (time constraints, panic triggers)
2. Authority Intimidation Index (police/CBI/CEO posture)
3. Secrecy & Isolation Index (refusal to allow second opinions)
4. Coercion Pressure Index (threats of arrest/termination)
"""

from typing import List, Tuple
from .models import PsychologicalIndicators
from .patterns import PSYCHOLOGICAL_MARKERS


class HeuristicEngine:
    """
    Quantifies psychological manipulation tactics used in voice scams.
    """

    def __init__(self):
        self.markers = PSYCHOLOGICAL_MARKERS

    def analyze(self, dialogue_text: str, is_caller: bool = True) -> PsychologicalIndicators:
        """
        Analyzes conversational text and computes normalized behavioral scores [0.0 - 1.0].
        """
        if not dialogue_text:
            return PsychologicalIndicators()

        words = dialogue_text.split()
        word_count = max(len(words), 10)

        # 1. Urgency Score
        urgency_matches = 0
        for regex in self.markers["urgency"]:
            urgency_matches += len(regex.findall(dialogue_text))
        urgency_score = min(1.0, (urgency_matches * 15.0) / word_count)

        # 2. Authority Intimidation Score
        authority_matches = 0
        for regex in self.markers["authority"]:
            authority_matches += len(regex.findall(dialogue_text))
        authority_score = min(1.0, (authority_matches * 18.0) / word_count)

        # 3. Secrecy & Isolation Score
        secrecy_matches = 0
        for regex in self.markers["secrecy_isolation"]:
            secrecy_matches += len(regex.findall(dialogue_text))
        secrecy_score = min(1.0, (secrecy_matches * 25.0) / word_count)

        # 4. Coercion / Threat Pressure Score
        coercion_matches = 0
        for regex in self.markers["coercion_threat"]:
            coercion_matches += len(regex.findall(dialogue_text))
        coercion_score = min(1.0, (coercion_matches * 20.0) / word_count)

        # Non-linear boost if multiple psychological vectors combine simultaneously
        num_vectors_present = sum(
            1 for s in [urgency_score, authority_score, secrecy_score, coercion_score] if s > 0.15
        )
        synergy_multiplier = 1.0 + (0.15 * max(0, num_vectors_present - 1))

        return PsychologicalIndicators(
            urgency_score=min(1.0, urgency_score * synergy_multiplier),
            authority_intimidation_score=min(1.0, authority_score * synergy_multiplier),
            secrecy_isolation_score=min(1.0, secrecy_score * synergy_multiplier),
            coercion_pressure_score=min(1.0, coercion_score * synergy_multiplier),
        )

    def calculate_aggregate_pressure(self, indicators: PsychologicalIndicators) -> float:
        """
        Computes composite social engineering pressure metric [0.0 - 1.0].
        """
        weights = [
            (indicators.urgency_score, 0.25),
            (indicators.authority_intimidation_score, 0.30),
            (indicators.secrecy_isolation_score, 0.25),
            (indicators.coercion_pressure_score, 0.20),
        ]
        return min(1.0, sum(score * w for score, w in weights))
