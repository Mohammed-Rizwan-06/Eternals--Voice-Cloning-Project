"""
VoxShield - Scam Intelligence Subsystem
Module Owner: Keerthi
Problem Statement #26104

Provides multi-layered real-time financial scam detection, social engineering
intent classification, psychological coercion analysis, and entity extraction.
"""

from .models import (
    ActionType,
    ExtractedFinancialEntities,
    MatchedPattern,
    PsychologicalIndicators,
    ScamAnalysisResult,
    ScamCategory,
    ThreatLevel,
    UrgencyLevel,
)
from .patterns import SCAM_PATTERNS, ENTITY_REGEXES
from .rule_engine import RuleEngine
from .heuristic_engine import HeuristicEngine
from .llm_analyzer import LLMContextAnalyzer, LocalSemanticAnalyzer
from .detector import FinancialScamDetector

__all__ = [
    "ActionType",
    "ExtractedFinancialEntities",
    "MatchedPattern",
    "PsychologicalIndicators",
    "ScamAnalysisResult",
    "ScamCategory",
    "ThreatLevel",
    "UrgencyLevel",
    "SCAM_PATTERNS",
    "ENTITY_REGEXES",
    "RuleEngine",
    "HeuristicEngine",
    "LLMContextAnalyzer",
    "LocalSemanticAnalyzer",
    "FinancialScamDetector",
]
