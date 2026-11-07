"""Pydantic Models and Schemas for Operations Copilot Squad."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CitationSourceType(str, Enum):
    LEDGER_SUMMARY = "LEDGER_SUMMARY"
    APPROVAL_INBOX = "APPROVAL_INBOX"
    FINANCIAL_CRIME_ALERT = "FINANCIAL_CRIME_ALERT"
    PAYMENT_EXCEPTION = "PAYMENT_EXCEPTION"
    SYSTEM_TELEMETRY = "SYSTEM_TELEMETRY"


class GroundedCitation(BaseModel):
    source_type: CitationSourceType
    entity_id: str
    metric_or_field: str
    verified_value: str
    citation_tag: str


class CopilotQueryRequest(BaseModel):
    query: str
    operator_id: str = "op_default_analyst"
    department: str = "GENERAL_OPERATIONS"


class SuggestedAction(BaseModel):
    label: str
    action_type: str  # NAVIGATE, TRIGGER_REVIEW, EXPORT
    target_url_or_id: str


class CopilotAnswer(BaseModel):
    query: str
    answer_markdown: str
    citations: List[GroundedCitation] = Field(default_factory=list)
    suggested_actions: List[SuggestedAction] = Field(default_factory=list)
    confidence: float = 1.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
