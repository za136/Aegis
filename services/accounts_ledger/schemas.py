"""Pydantic v2 schemas and validation contracts for Double-Entry Ledger."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from services.accounts_ledger.models import (
    AccountStatus,
    AccountType,
    HoldStatus,
    JournalEntryStatus,
    PostingDirection,
)


class AccountCreateRequest(BaseModel):
    """Payload to create a new ledger account."""
    model_config = ConfigDict(frozen=True)

    owner_id: str = Field(..., min_length=1, max_length=64, description="Customer or Entity ID")
    name: str = Field(..., min_length=1, max_length=128, description="Human-readable account label")
    account_type: AccountType = Field(default=AccountType.LIABILITY)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    account_number: Optional[str] = Field(None, max_length=34)


class AccountResponse(BaseModel):
    """Public account summary response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_number: str
    owner_id: str
    name: str
    account_type: AccountType
    currency: str
    status: AccountStatus
    settled_balance: Decimal
    pending_incoming: Decimal
    reserved_outgoing: Decimal
    available_balance: Decimal
    created_at: datetime
    updated_at: datetime


class PostingRequest(BaseModel):
    """Single leg of a double-entry journal entry."""
    model_config = ConfigDict(frozen=True)

    account_id: uuid.UUID
    amount: Decimal = Field(..., gt=Decimal("0.0000"), description="Positive decimal transaction amount")
    direction: PostingDirection = Field(..., description="DEBIT or CREDIT")

    @field_validator("amount")
    @classmethod
    def validate_precision(cls, v: Decimal) -> Decimal:
        """Round and ensure precision is within banking decimal scale."""
        return v.quantize(Decimal("0.0001"))


class PostingResponse(BaseModel):
    """Detailed posting leg response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    journal_entry_id: uuid.UUID
    account_id: uuid.UUID
    amount: Decimal
    direction: PostingDirection
    sequence: int


class JournalEntryRequest(BaseModel):
    """Atomic multi-leg double-entry request with zero-sum invariant assertion."""
    model_config = ConfigDict(frozen=True)

    idempotency_key: str = Field(..., min_length=8, max_length=128)
    transaction_type: str = Field(..., min_length=2, max_length=64)
    description: str = Field(..., min_length=2, max_length=256)
    postings: List[PostingRequest] = Field(..., min_length=2, description="At least two balanced posting legs")

    @model_validator(mode="after")
    def assert_zero_sum_balance(self) -> "JournalEntryRequest":
        """Strict double-entry balancing invariant: Sum(Debits) must equal Sum(Credits)."""
        total_debit = Decimal("0.0000")
        total_credit = Decimal("0.0000")

        for posting in self.postings:
            if posting.direction == PostingDirection.DEBIT:
                total_debit += posting.amount
            elif posting.direction == PostingDirection.CREDIT:
                total_credit += posting.amount

        if total_debit != total_credit:
            raise ValueError(
                f"Double-entry invariant violated: Total Debits ({total_debit}) != "
                f"Total Credits ({total_credit}). Imbalance delta: {total_debit - total_credit}"
            )
        return self


class JournalEntryResponse(BaseModel):
    """Complete journal entry response including all line items."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    idempotency_key: str
    transaction_type: str
    description: str
    status: JournalEntryStatus
    posted_at: datetime
    postings: List[PostingResponse]


class InternalTransferRequest(BaseModel):
    """Simplified customer transfer request between two ledger accounts."""
    model_config = ConfigDict(frozen=True)

    idempotency_key: str = Field(..., min_length=8, max_length=128)
    source_account_id: uuid.UUID
    destination_account_id: uuid.UUID
    amount: Decimal = Field(..., gt=Decimal("0.0000"))
    currency: str = Field(default="USD", min_length=3, max_length=3)
    description: str = Field(default="Internal account transfer", max_length=256)

    @field_validator("destination_account_id")
    @classmethod
    def assert_different_accounts(cls, v: uuid.UUID, info) -> uuid.UUID:
        if "source_account_id" in info.data and v == info.data["source_account_id"]:
            raise ValueError("Source and destination accounts must be distinct.")
        return v


class HoldRequest(BaseModel):
    """Request to create a balance reservation hold."""
    model_config = ConfigDict(frozen=True)

    account_id: uuid.UUID
    amount: Decimal = Field(..., gt=Decimal("0.0000"))
    currency: str = Field(default="USD", min_length=3, max_length=3)
    reference: str = Field(..., min_length=4, max_length=128)
    ttl_seconds: Optional[int] = Field(default=86400, gt=0, description="Hold expiration in seconds")


class HoldResponse(BaseModel):
    """Hold reservation status response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    amount: Decimal
    currency: str
    status: HoldStatus
    reference: str
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
