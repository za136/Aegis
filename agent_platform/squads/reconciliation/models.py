"""Pydantic Models and Schemas for B2B Invoice Reconciliation Squad."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class InvoiceStatus(str, Enum):
    UNPAID = "UNPAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    DISPUTED = "DISPUTED"


class MatchType(str, Enum):
    EXACT_ONE_TO_ONE = "EXACT_ONE_TO_ONE"
    FUZZY_REFERENCE = "FUZZY_REFERENCE"
    SPLIT_PAYMENT_COMBINED = "SPLIT_PAYMENT_COMBINED"  # 1 remittance paying 2+ invoices
    PARTIAL_PAYMENT = "PARTIAL_PAYMENT"               # payment < invoice amount
    UNMATCHED = "UNMATCHED"


class Invoice(BaseModel):
    invoice_id: str
    vendor_id: str
    customer_id: str
    invoice_number: str
    amount: Decimal = Field(..., gt=0)
    currency: str = "USD"
    issue_date: date
    due_date: date
    status: InvoiceStatus = InvoiceStatus.UNPAID
    paid_amount: Decimal = Decimal("0.00")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LedgerPostingItem(BaseModel):
    posting_id: str
    account_id: str
    amount: Decimal
    direction: str  # CREDIT or DEBIT
    narrative: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    currency: str = "USD"
    reconciled: bool = False


class RemittanceAdvice(BaseModel):
    remittance_id: str
    payer_name: str
    payee_name: str
    total_amount: Decimal
    currency: str = "USD"
    stated_invoice_numbers: List[str] = Field(default_factory=list)
    raw_memo: str
    received_at: datetime = Field(default_factory=datetime.utcnow)


class ReconciliationMatch(BaseModel):
    match_id: str
    match_type: MatchType
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    matched_invoice_ids: List[str] = Field(default_factory=list)
    matched_posting_ids: List[str] = Field(default_factory=list)
    total_invoice_amount: Decimal
    total_posting_amount: Decimal
    discrepancy_amount: Decimal = Decimal("0.00")
    rationale: str
    approved: bool = False


class ReconciliationBatch(BaseModel):
    batch_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    matches: List[ReconciliationMatch] = Field(default_factory=list)
    unmatched_postings: List[str] = Field(default_factory=list)
    unmatched_invoices: List[str] = Field(default_factory=list)
    total_matched_volume: Decimal = Decimal("0.00")
    status: str = "DRAFT"  # DRAFT, APPROVED, APPLIED
