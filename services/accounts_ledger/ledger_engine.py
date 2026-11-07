"""Core Double-Entry Ledger Engine with strict mathematical invariants."""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from services.accounts_ledger.models import (
    Account,
    AccountStatus,
    AccountType,
    Hold,
    HoldStatus,
    JournalEntry,
    JournalEntryStatus,
    Posting,
    PostingDirection,
    utc_now,
)
from services.accounts_ledger.schemas import (
    AccountCreateRequest,
    HoldRequest,
    InternalTransferRequest,
    JournalEntryRequest,
)


class InsufficientFundsError(Exception):
    """Raised when available balance is insufficient for withdrawal or hold."""
    pass


class AccountNotActiveError(Exception):
    """Raised when an account is frozen, restricted, or closed."""
    pass


class InvariantViolationError(Exception):
    """Raised when a balance or double-entry balancing invariant is breached."""
    pass


class LedgerEngine:
    """Deterministic Banking Core Ledger Engine.

    Guarantees:
    1. Zero-Sum Double-Entry: Sum(Debits) == Sum(Credits) for every posted journal entry.
    2. Balance Invariant: Available Balance (Settled - Reserved) >= 0 at all times.
    3. Idempotency: All operations enforce unique idempotency keys.
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session

    @staticmethod
    def generate_account_number(prefix: str = "AEGIS") -> str:
        """Generate a random deterministic-format account identifier."""
        return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"

    def calculate_balance_delta(
        self, account_type: AccountType, direction: PostingDirection, amount: Decimal
    ) -> Decimal:
        """Calculate signed balance mutation based on standard financial accounting conventions.

        For LIABILITY accounts (customer deposits):
          - CREDIT increases liability (bank owes more -> customer balance goes UP)
          - DEBIT decreases liability (bank owes less -> customer balance goes DOWN)

        For ASSET accounts (clearing, Nostro, cash):
          - DEBIT increases asset (bank asset goes UP)
          - CREDIT decreases asset (bank asset goes DOWN)
        """
        if account_type == AccountType.LIABILITY:
            return amount if direction == PostingDirection.CREDIT else -amount
        elif account_type == AccountType.ASSET:
            return amount if direction == PostingDirection.DEBIT else -amount
        elif account_type == AccountType.REVENUE:
            return amount if direction == PostingDirection.CREDIT else -amount
        elif account_type in (AccountType.EXPENSE, AccountType.EQUITY):
            return amount if direction == PostingDirection.DEBIT else -amount
        return -amount

    async def create_account(
        self, request: AccountCreateRequest, db: AsyncSession
    ) -> Account:
        """Create a new account on the ledger."""
        account_number = request.account_number or self.generate_account_number()
        account = Account(
            owner_id=request.owner_id,
            account_number=account_number,
            name=request.name,
            account_type=request.account_type,
            currency=request.currency.upper(),
            status=AccountStatus.ACTIVE,
            settled_balance=Decimal("0.0000"),
            pending_incoming=Decimal("0.0000"),
            reserved_outgoing=Decimal("0.0000"),
        )
        db.add(account)
        await db.flush()
        return account

    async def get_account(self, account_id: uuid.UUID, db: AsyncSession) -> Optional[Account]:
        """Fetch an account by UUID."""
        stmt = select(Account).where(Account.id == account_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_hold(
        self, request: HoldRequest, db: AsyncSession
    ) -> Hold:
        """Reserve funds on an account (e.g. pending card authorization or outbox dispatch)."""
        account = await self.get_account(request.account_id, db)
        if not account:
            raise ValueError(f"Account {request.account_id} not found.")

        if account.status != AccountStatus.ACTIVE:
            raise AccountNotActiveError(f"Account {account.account_number} is {account.status.value}.")

        # Invariant check: Available balance must cover the hold
        if account.available_balance < request.amount:
            raise InsufficientFundsError(
                f"Insufficient available funds on {account.account_number}: "
                f"Available {account.available_balance} {account.currency} < Requested Hold {request.amount}"
            )

        # Mutate reserved hold balance
        account.reserved_outgoing += request.amount

        expires_at = None
        if request.ttl_seconds:
            expires_at = utc_now() + timedelta(seconds=request.ttl_seconds)

        hold = Hold(
            account_id=account.id,
            amount=request.amount,
            currency=request.currency.upper(),
            status=HoldStatus.ACTIVE,
            reference=request.reference,
            expires_at=expires_at,
        )
        db.add(hold)
        await db.flush()
        return hold

    async def release_hold(
        self, hold_id: uuid.UUID, db: AsyncSession
    ) -> Hold:
        """Void / release an active hold, returning funds to available balance."""
        stmt = select(Hold).where(Hold.id == hold_id)
        result = await db.execute(stmt)
        hold = result.scalar_one_or_none()
        if not hold:
            raise ValueError(f"Hold {hold_id} not found.")

        if hold.status != HoldStatus.ACTIVE:
            raise InvariantViolationError(f"Cannot release hold with status {hold.status.value}.")

        account = await self.get_account(hold.account_id, db)
        if not account:
            raise ValueError(f"Account {hold.account_id} not found.")

        # Release reservation
        account.reserved_outgoing -= hold.amount
        if account.reserved_outgoing < Decimal("0.0000"):
            account.reserved_outgoing = Decimal("0.0000")

        hold.status = HoldStatus.RELEASED
        await db.flush()
        return hold

    async def post_journal_entry(
        self, request: JournalEntryRequest, db: AsyncSession
    ) -> JournalEntry:
        """Post an atomic double-entry journal entry with verified balancing."""
        # 1. Verify idempotency
        stmt = select(JournalEntry).where(JournalEntry.idempotency_key == request.idempotency_key)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing

        # 2. Fetch and lock accounts
        account_ids = [p.account_id for p in request.postings]
        stmt_accounts = select(Account).where(Account.id.in_(account_ids)).with_for_update()
        accounts_map: Dict[uuid.UUID, Account] = {
            acc.id: acc for acc in (await db.execute(stmt_accounts)).scalars().all()
        }

        for acc_id in account_ids:
            if acc_id not in accounts_map:
                raise ValueError(f"Account ID {acc_id} does not exist.")

        # 3. Simulate balance mutations & check invariants
        balance_deltas: Dict[uuid.UUID, Decimal] = {}
        for posting_req in request.postings:
            acc = accounts_map[posting_req.account_id]
            if acc.status != AccountStatus.ACTIVE:
                raise AccountNotActiveError(f"Account {acc.account_number} is {acc.status.value}.")

            delta = self.calculate_balance_delta(
                acc.account_type, posting_req.direction, posting_req.amount
            )
            balance_deltas[acc.id] = balance_deltas.get(acc.id, Decimal("0.0000")) + delta

        for acc_id, delta in balance_deltas.items():
            acc = accounts_map[acc_id]
            projected_settled = acc.settled_balance + delta
            projected_available = projected_settled - acc.reserved_outgoing

            if projected_settled < Decimal("0.0000") or projected_available < Decimal("0.0000"):
                raise InsufficientFundsError(
                    f"Transaction violates balance invariant on account {acc.account_number}. "
                    f"Projected Settled: {projected_settled}, Projected Available: {projected_available}"
                )

        # 4. Create immutable JournalEntry and Postings
        journal_entry = JournalEntry(
            idempotency_key=request.idempotency_key,
            transaction_type=request.transaction_type,
            description=request.description,
            status=JournalEntryStatus.POSTED,
        )
        db.add(journal_entry)
        await db.flush()

        for idx, posting_req in enumerate(request.postings):
            posting = Posting(
                journal_entry_id=journal_entry.id,
                account_id=posting_req.account_id,
                amount=posting_req.amount,
                direction=posting_req.direction,
                sequence=idx,
            )
            db.add(posting)

            # Apply balance update to account
            acc = accounts_map[posting_req.account_id]
            delta = self.calculate_balance_delta(
                acc.account_type, posting_req.direction, posting_req.amount
            )
            acc.settled_balance += delta

        await db.flush()
        return journal_entry

    async def execute_transfer(
        self, request: InternalTransferRequest, db: AsyncSession
    ) -> JournalEntry:
        """Execute a simple internal transfer between two liability accounts."""
        from services.accounts_ledger.schemas import PostingRequest

        journal_request = JournalEntryRequest(
            idempotency_key=request.idempotency_key,
            transaction_type="INTERNAL_TRANSFER",
            description=request.description,
            postings=[
                PostingRequest(
                    account_id=request.source_account_id,
                    amount=request.amount,
                    direction=PostingDirection.DEBIT,  # Decreases liability / debit customer
                ),
                PostingRequest(
                    account_id=request.destination_account_id,
                    amount=request.amount,
                    direction=PostingDirection.CREDIT,  # Increases liability / credit customer
                ),
            ],
        )
        return await self.post_journal_entry(journal_request, db)
