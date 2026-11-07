"""SQLAlchemy models for Payments, Payment Lifecycle Saga, and Audit History."""

import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    JSON,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.accounts_ledger.models import Base, utc_now


class PaymentStatus(str, enum.Enum):
    """Payment lifecycle states per ISO 20022 banking saga."""
    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    SCREENING = "SCREENING"
    PENDING = "PENDING"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    FUNDS_RESERVED = "FUNDS_RESERVED"
    SUBMITTED = "SUBMITTED"
    SETTLED = "SETTLED"
    REJECTED = "REJECTED"
    RETURNED = "RETURNED"
    FAILED = "FAILED"


class PaymentInstruction(BaseModel):
    """Lightweight instruction payload for bulk batch simulation & messaging."""
    payment_id: str
    source_account_id: str
    destination_account_id: str
    amount: Decimal
    currency: str = "USD"
    reference: str = ""
    status: PaymentStatus = PaymentStatus.PENDING


class Payment(Base):
    """Payment instruction representing customer transfer through the banking lifecycle."""
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    debtor_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    creditor_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    creditor_account_number: Mapped[str] = mapped_column(String(34), nullable=False)
    creditor_name: Mapped[str] = mapped_column(String(128), nullable=False)

    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    description: Mapped[str] = mapped_column(String(256), nullable=False)

    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), nullable=False, default=PaymentStatus.CREATED, index=True
    )

    # Reference to ledger hold during RESERVED phase
    hold_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("holds.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Reference to final posted journal entry upon settlement
    journal_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal_entries.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ISO 20022 exception codes (for payment exception repair squad)
    rejection_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    # Full audit history of state transitions
    state_history: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_payment_amount_positive"),
    )

    def transition_to(
        self, new_status: PaymentStatus, reason: Optional[str] = None
    ) -> None:
        """Record state machine transition with audit timestamp."""
        transition_record = {
            "from_status": self.status.value,
            "to_status": new_status.value,
            "timestamp": utc_now().isoformat(),
            "reason": reason,
        }
        self.status = new_status
        # Ensure state_history is updated
        history = list(self.state_history)
        history.append(transition_record)
        self.state_history = history
