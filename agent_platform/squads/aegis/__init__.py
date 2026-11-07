"""Aegis Financial Crime Investigation Squad package."""

from agent_platform.squads.aegis.agent import AegisInvestigationAgent
from agent_platform.squads.aegis.analyzer import TransactionAnalyzer, analyzer
from agent_platform.squads.aegis.guardrails import scan_for_prompt_injection, sanitize_input
from agent_platform.squads.aegis.models import (
    AlertPriority,
    AlertTypology,
    CaseEvidence,
    CaseNarrative,
    InvestigationCase,
    InvestigationPlan,
    PolicyExcerpt,
    RecommendedDisposition,
    TransactionFinding,
    TriageResult,
    VerificationResult,
)
from agent_platform.squads.aegis.policy_rag import retrieve_policies
from agent_platform.squads.aegis.verifier import NarrativeVerifier, verifier

__all__ = [
    "AegisInvestigationAgent",
    "TransactionAnalyzer",
    "analyzer",
    "scan_for_prompt_injection",
    "sanitize_input",
    "AlertPriority",
    "AlertTypology",
    "CaseEvidence",
    "CaseNarrative",
    "InvestigationCase",
    "InvestigationPlan",
    "PolicyExcerpt",
    "RecommendedDisposition",
    "TransactionFinding",
    "TriageResult",
    "VerificationResult",
    "retrieve_policies",
    "NarrativeVerifier",
    "verifier",
]
