"""Pydantic v2 schemas for Payment Initiation, Responses, and Repair Actions."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from services.payments.models import PaymentStatus


class PaymentCreateRequest(BaseModel):
    """Payment initiation instruction payload."""
    model_config = ConfigDict(frozen=True)

    idempotency_key: str = Field(..., min_length=8, max_length=128)
    debtor_account_id: uuid.UUID
    creditor_account_number: str = Field(..., min_length=4, max_length=34)
    creditor_name: str = Field(..., min_length=1, max_length=128)
    amount: Decimal = Field(..., gt=Decimal("0.0000"))
    currency: str = Field(default="USD", min_length=3, max_length=3)
    description: str = Field(default="Payment transfer", max_length=256)


class PaymentResponse(BaseModel):
    """Full payment instruction status and lifecycle audit response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    idempotency_key: str
    debtor_account_id: uuid.UUID
    creditor_account_id: Optional[uuid.UUID]
    creditor_account_number: str
    creditor_name: str
    amount: Decimal
    currency: str
    description: str
    status: PaymentStatus
    hold_id: Optional[uuid.UUID]
    journal_entry_id: Optional[uuid.UUID]
    rejection_code: Optional[str]
    rejection_reason: Optional[str]
    state_history: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class PaymentRepairRequest(BaseModel):
    """Payload submitted by the Payment Exception Repair squad to fix stuck/rejected transfers."""
    model_config = ConfigDict(frozen=True)

    payment_id: uuid.UUID
    corrected_account_number: Optional[str] = None
    corrected_creditor_name: Optional[str] = None
    repair_reason: str = Field(..., min_length=5, max_length=256)
    action_type: str = Field(default="RESUBMIT", description="RESUBMIT | RETURN_FUNDS | CANCEL")
