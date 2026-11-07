"""SQLAlchemy 2.0 async domain models for Double-Entry Ledger."""

import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""
    pass


class AccountType(str, enum.Enum):
    """Standard Chart of Accounts classification."""
    ASSET = "ASSET"          # Bank assets (clearing accounts, loans)
    LIABILITY = "LIABILITY"  # Customer deposits (positive balance = bank owes customer)
    EQUITY = "EQUITY"        # Bank capital & retained earnings
    REVENUE = "REVENUE"      # Fees, interest earned
    EXPENSE = "EXPENSE"      # Operating costs, network fees


class AccountStatus(str, enum.Enum):
    """Lifecycle status of a financial account."""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    RESTRICTED = "RESTRICTED"
    CLOSED = "CLOSED"


class PostingDirection(str, enum.Enum):
    """Direction of a double-entry line item."""
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class JournalEntryStatus(str, enum.Enum):
    """Status of an immutable journal entry."""
    POSTED = "POSTED"
    REVERSED = "REVERSED"


class HoldStatus(str, enum.Enum):
    """Lifecycle status of a two-phase balance reservation hold."""
    ACTIVE = "ACTIVE"
    CAPTURED = "CAPTURED"    # Settled into a posted journal entry
    RELEASED = "RELEASED"    # Voided / unheld
    EXPIRED = "EXPIRED"


class Account(Base):
    """Financial account representing an entity on the ledger."""
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_number: Mapped[str] = mapped_column(
        String(34), unique=True, nullable=False, index=True
    )
    owner_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    account_type: Mapped[AccountType] = mapped_column(
        Enum(AccountType), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus), nullable=False, default=AccountStatus.ACTIVE
    )

    # Balance tracking columns (cached materialized figures backed by ledger entries)
    settled_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=Decimal("0.0000")
    )
    pending_incoming: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=Decimal("0.0000")
    )
    reserved_outgoing: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=Decimal("0.0000")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    # Relationships
    postings: Mapped[List["Posting"]] = relationship("Posting", back_populates="account")
    holds: Mapped[List["Hold"]] = relationship("Hold", back_populates="account")

    __table_args__ = (
        CheckConstraint("settled_balance >= 0", name="chk_account_settled_non_negative"),
        CheckConstraint("reserved_outgoing >= 0", name="chk_account_reserved_non_negative"),
        CheckConstraint(
            "settled_balance - reserved_outgoing >= 0",
            name="chk_account_available_non_negative"
        ),
    )

    @property
    def available_balance(self) -> Decimal:
        """Available balance = settled balance minus reserved holds."""
        return self.settled_balance - self.reserved_outgoing


class JournalEntry(Base):
    """Immutable ledger transaction record containing balanced debit and credit postings."""
    __tablename__ = "journal_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    transaction_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[JournalEntryStatus] = mapped_column(
        Enum(JournalEntryStatus), nullable=False, default=JournalEntryStatus.POSTED
    )
    posted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, index=True
    )

    # Relationships
    postings: Mapped[List["Posting"]] = relationship(
        "Posting", back_populates="journal_entry", cascade="all, delete-orphan"
    )


class Posting(Base):
    """Atomic double-entry leg (debit or credit). Sum(Debits) must equal Sum(Credits)."""
    __tablename__ = "postings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    journal_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal_entries.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False
    )
    direction: Mapped[PostingDirection] = mapped_column(
        Enum(PostingDirection), nullable=False
    )
    sequence: Mapped[int] = mapped_column(nullable=False, default=0)

    # Relationships
    journal_entry: Mapped["JournalEntry"] = relationship("JournalEntry", back_populates="postings")
    account: Mapped["Account"] = relationship("Account", back_populates="postings")

    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_posting_amount_positive"),
        Index("ix_postings_account_journal", "account_id", "journal_entry_id"),
    )


class Hold(Base):
    """Two-phase funds reservation (e.g. pending payment network authorization)."""
    __tablename__ = "holds"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[HoldStatus] = mapped_column(
        Enum(HoldStatus), nullable=False, default=HoldStatus.ACTIVE, index=True
    )
    reference: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="holds")

    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_hold_amount_positive"),
    )


class BalanceSnapshot(Base):
    """Point-in-time balance snapshot for high-throughput query performance."""
    __tablename__ = "balance_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    last_journal_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    settled_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False
    )
    snapshot_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, index=True
    )
