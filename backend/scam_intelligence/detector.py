"""
VoxShield - Unified Financial Scam Detector
Module: backend.scam_intelligence.detector
Owner: Keerthi
Problem Statement #26104

Integrates RuleEngine, HeuristicEngine, and LLMContextAnalyzer.
Synthesizes comprehensive ScamAnalysisResult ready for consumption
by Yash's Risk Engine (risk fusion) and Mohit's Frontend.
"""

import asyncio
from typing import Dict, List, Optional
from .models import (
    ActionType,
    ExtractedFinancialEntities,
    PsychologicalIndicators,
    ScamAnalysisResult,
    ScamCategory,
    ThreatLevel,
)
from .rule_engine import RuleEngine
from .heuristic_engine import HeuristicEngine
from .llm_analyzer import LLMContextAnalyzer


class FinancialScamDetector:
    """
    Main entry point for Keerthi's Scam Intelligence subsystem.
    Processes conversational transcripts and emits structured threat evaluations.
    """

    def __init__(
        self,
        llm_api_key: Optional[str] = None,
        llm_provider: str = "auto"
    ):
        self.rule_engine = RuleEngine()
        self.heuristic_engine = HeuristicEngine()
        self.llm_analyzer = LLMContextAnalyzer(api_key=llm_api_key, provider=llm_provider)

    async def analyze_transcript(
        self,
        session_id: str,
        transcript_text: str,
        dialogue_turns: Optional[List[dict]] = None
    ) -> ScamAnalysisResult:
        """
        Executes multi-layered scam intelligence analysis on the transcript.
        1. Fast Rule & Pattern Matching (<5ms)
        2. Financial Entity Extraction
        3. Psychological & Coercion Heuristics
        4. Contextual Semantic Evaluation
        5. Fused Score & Recommendation Synthesis
        """
        if not transcript_text or not transcript_text.strip():
            return ScamAnalysisResult(
                session_id=session_id,
                overall_scam_score=0.0,
                threat_level=ThreatLevel.BENIGN,
                primary_scam_type=ScamCategory.BENIGN,
                confidence=1.0,
                is_imminent_threat=False,
                explanation="No speech audio detected in call yet.",
                recommended_action="Monitoring call...",
                action_type=ActionType.NO_ACTION,
            )

        # Step 1: Rule Engine Evaluation
        matched_patterns, category_scores, imminent_threat = self.rule_engine.evaluate(transcript_text)
        entities = self.rule_engine.extract_entities(transcript_text)

        # Step 2: Psychological Coercion Heuristics
        psych_indicators = self.heuristic_engine.analyze(transcript_text)
        pressure_score = self.heuristic_engine.calculate_aggregate_pressure(psych_indicators)

        # Step 3: Contextual Semantic Reasoning
        llm_verdict = await self.llm_analyzer.analyze(
            transcript_text=transcript_text,
            category_scores=category_scores,
            pressure_score=pressure_score,
            imminent_threat=imminent_threat,
        )

        # Step 4: Multi-Layer Score Fusion
        # Calculate raw category score from matched rules
        top_rule_score = max(category_scores.values()) if category_scores else 0.0

        # Weighted calculation for Keerthi's financial scam score:
        # 50% Rule Evidence + 25% Psychological Pressure + 25% Contextual Reasoning
        raw_score = (
            (min(1.0, top_rule_score) * 0.50) +
            (pressure_score * 0.25) +
            ((1.0 if llm_verdict["is_scam"] else 0.0) * 0.25)
        )

        # High danger threshold override: If imminent critical trigger is present, floor score at 0.88
        if imminent_threat:
            raw_score = max(raw_score, 0.88)

        overall_score = min(1.0, max(0.0, raw_score))

        # Step 5: Threat Level Classification
        if overall_score >= 0.80:
            threat_level = ThreatLevel.CRITICAL
        elif overall_score >= 0.60:
            threat_level = ThreatLevel.HIGH
        elif overall_score >= 0.35:
            threat_level = ThreatLevel.MEDIUM
        elif overall_score >= 0.15:
            threat_level = ThreatLevel.LOW
        else:
            threat_level = ThreatLevel.BENIGN

        primary_type_str = llm_verdict.get("primary_scam_type", ScamCategory.BENIGN.value)
        try:
            primary_scam_type = ScamCategory(primary_type_str)
        except Exception:
            primary_scam_type = ScamCategory.BENIGN

        action_type_str = llm_verdict.get("action_type", ActionType.NO_ACTION.value)
        try:
            action_type = ActionType(action_type_str)
        except Exception:
            action_type = ActionType.NO_ACTION

        return ScamAnalysisResult(
            session_id=session_id,
            overall_scam_score=overall_score,
            threat_level=threat_level,
            primary_scam_type=primary_scam_type,
            confidence=llm_verdict.get("confidence", 0.90),
            is_imminent_threat=imminent_threat,
            matched_patterns=matched_patterns,
            extracted_entities=entities,
            psychological_indicators=psych_indicators,
            explanation=llm_verdict.get("explanation", ""),
            recommended_action=llm_verdict.get("recommended_action", ""),
            action_type=action_type,
        )
