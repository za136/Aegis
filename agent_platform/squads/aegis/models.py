"""Pydantic schemas for the Aegis Financial Crime Investigation Squad."""

import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AlertTypology(str, enum.Enum):
    STRUCTURING = "STRUCTURING"
    RAPID_MOVEMENT = "RAPID_MOVEMENT"
    LAYERING = "LAYERING"
    SANCTIONS_HIT = "SANCTIONS_HIT"
    MULE_ACTIVITY = "MULE_ACTIVITY"
    UNUSUAL_VOLUME = "UNUSUAL_VOLUME"


class AlertPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RecommendedDisposition(str, enum.Enum):
    FILE_SAR = "FILE_SAR"                            # File Suspicious Activity Report
    CLOSE_NO_ACTION = "CLOSE_NO_ACTION"              # Benign business activity, close alert
    REQUEST_RFI = "REQUEST_RFI"                      # Request for Information from customer
    ESCALATE_TO_LE = "ESCALATE_TO_LAW_ENFORCEMENT"   # Urgent law enforcement referral


class TriageResult(BaseModel):
    """Initial triage assessment determining typology, priority, and step budget."""
    alert_id: str
    typology: AlertTypology
    priority: AlertPriority
    confidence: float
    fast_close_plausible: bool
    initial_rationale: str


class InvestigationPlan(BaseModel):
    """Investigation strategy formulated by the planner agent."""
    case_id: str
    steps: List[str]
    step_budget: int = 5
    token_budget: int = 8000
    evidence_types_required: List[str]


class TransactionFinding(BaseModel):
    """Detected suspicious transaction pattern."""
    finding_id: str
    typology: AlertTypology
    description: str
    involved_transaction_ids: List[str]
    amount_total: Decimal
    time_window_hours: float
    evidence_id: str


class PolicyExcerpt(BaseModel):
    """Retrieved policy clause from the anti-money laundering knowledge corpus."""
    excerpt_id: str
    policy_name: str
    section: str
    citation: str
    content: str
    relevance_score: float


class CaseEvidence(BaseModel):
    """Evidence item tagged with a unique evidence ID for mandatory narrative citation."""
    evidence_id: str
    source_type: str  # TRANSACTION_PATTERN, WATCHLIST_SCREENING, POLICY_RULE, REGISTRY_CHECK
    summary: str
    raw_data: Dict[str, Any]
    recorded_at: datetime = Field(default_factory=utc_now)


class CaseNarrative(BaseModel):
    """Formal SAR narrative drafted with strict evidence citations."""
    case_id: str
    executive_summary: str
    detailed_chronology: str
    cited_evidence_ids: List[str]
    cited_policy_sections: List[str]
    recommended_disposition: RecommendedDisposition
    disposition_rationale: str
    drafter: str = "Aegis Narrative Agent (Gemini 3.8 Flash)"


class VerificationResult(BaseModel):
    """Adversarial verifier judgment checking that all assertions cite valid evidence."""
    status: str  # PASS or FAIL
    verified: bool
    checked_claims_count: int
    unsupported_claims: List[str] = Field(default_factory=list)
    missing_evidence_ids: List[str] = Field(default_factory=list)
    verifier_notes: str


class InvestigationCase(BaseModel):
    """Comprehensive financial crime investigation dossier."""
    case_id: str
    alert_id: str
    customer_id: str
    account_number: str
    typology: AlertTypology
    priority: AlertPriority
    status: str  # OPEN, IN_PROGRESS, PENDING_APPROVAL, CLOSED_SAR, CLOSED_NO_ACTION
    triage: Optional[TriageResult] = None
    plan: Optional[InvestigationPlan] = None
    findings: List[TransactionFinding] = Field(default_factory=list)
    evidence_store: Dict[str, CaseEvidence] = Field(default_factory=dict)
    policy_citations: List[PolicyExcerpt] = Field(default_factory=list)
    narrative: Optional[CaseNarrative] = None
    verification: Optional[VerificationResult] = None
    approval_ticket_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    completed_at: Optional[datetime] = None
