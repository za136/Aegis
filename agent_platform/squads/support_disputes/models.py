"""Pydantic Models and Schemas for Customer Support & Payment Disputes Squad."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DisputeReason(str, Enum):
    UNAUTHORIZED_TRANSACTION = "UNAUTHORIZED_TRANSACTION"
    GOODS_SERVICES_NOT_RECEIVED = "GOODS_SERVICES_NOT_RECEIVED"
    DEFECTIVE_OR_NOT_AS_DESCRIBED = "DEFECTIVE_OR_NOT_AS_DESCRIBED"
    DUPLICATE_PROCESSING = "DUPLICATE_PROCESSING"
    INCORRECT_AMOUNT = "INCORRECT_AMOUNT"


class DisputeStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    PROVISIONAL_CREDIT_GRANTED = "PROVISIONAL_CREDIT_GRANTED"
    RESOLVED_CUSTOMER_FAVOR = "RESOLVED_CUSTOMER_FAVOR"
    RESOLVED_MERCHANT_FAVOR = "RESOLVED_MERCHANT_FAVOR"
    ESCALATED_CHARGEBACK = "ESCALATED_CHARGEBACK"


class DisputeClaim(BaseModel):
    claim_id: str
    account_id: str
    transaction_id: str
    is_consumer_account: bool = True
    dispute_amount: Decimal = Field(..., gt=0)
    dispute_reason: DisputeReason
    customer_statement: str
    transaction_date: date
    statement_date: date
    reported_date: date
    card_compromise_learned_date: Optional[date] = None
    status: DisputeStatus = DisputeStatus.SUBMITTED
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RegEAssessment(BaseModel):
    claim_id: str
    is_reg_e_eligible: bool
    within_60_day_window: bool
    days_since_statement: int
    days_to_notice: int
    consumer_max_liability: Decimal
    provisional_credit_mandated: bool
    provisional_credit_deadline_days: int = 10
    statutory_citation: str = "12 C.F.R. § 1005 (Regulation E)"
    reasoning: str


class DisputeResolution(BaseModel):
    claim_id: str
    status: DisputeStatus
    provisional_credit_amount: Decimal = Decimal("0.00")
    chargeback_reason_code: Optional[str] = None
    investigation_summary: str
    approval_ticket_id: Optional[str] = None
    final_credit_amount: Decimal = Decimal("0.00")
