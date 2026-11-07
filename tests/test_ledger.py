"""Unit tests for Double-Entry Ledger models, schemas and invariants."""

import uuid
from decimal import Decimal
import pytest
from pydantic import ValidationError

from services.accounts_ledger.models import (
    Account,
    AccountStatus,
    AccountType,
    PostingDirection,
)
from services.accounts_ledger.schemas import (
    JournalEntryRequest,
    PostingRequest,
    InternalTransferRequest,
)


def test_double_entry_balanced_passes():
    """Test that a balanced 2-leg journal entry succeeds validation."""
    acc_1 = uuid.uuid4()
    acc_2 = uuid.uuid4()

    entry = JournalEntryRequest(
        idempotency_key="test_idem_001_balanced",
        transaction_type="INTERNAL_TRANSFER",
        description="Transfer between customer accounts",
        postings=[
            PostingRequest(
                account_id=acc_1,
                amount=Decimal("150.00"),
                direction=PostingDirection.DEBIT,
            ),
            PostingRequest(
                account_id=acc_2,
                amount=Decimal("150.00"),
                direction=PostingDirection.CREDIT,
            ),
        ],
    )
    assert entry.idempotency_key == "test_idem_001_balanced"
    assert len(entry.postings) == 2


def test_double_entry_unbalanced_fails():
    """Test that an unbalanced journal entry strictly fails with validation error."""
    acc_1 = uuid.uuid4()
    acc_2 = uuid.uuid4()

    with pytest.raises(ValidationError) as exc_info:
        JournalEntryRequest(
            idempotency_key="test_idem_002_unbalanced",
            transaction_type="INTERNAL_TRANSFER",
            description="Unbalanced transfer attempt",
            postings=[
                PostingRequest(
                    account_id=acc_1,
                    amount=Decimal("150.00"),
                    direction=PostingDirection.DEBIT,
                ),
                PostingRequest(
                    account_id=acc_2,
                    amount=Decimal("140.00"),  # $10 discrepancy!
                    direction=PostingDirection.CREDIT,
                ),
            ],
        )

    assert "Double-entry invariant violated" in str(exc_info.value)


def test_multi_leg_split_transfer_balanced():
    """Test a 3-leg split transaction (e.g. 1 debit split into 2 credits)."""
    payer = uuid.uuid4()
    vendor = uuid.uuid4()
    fee_account = uuid.uuid4()

    entry = JournalEntryRequest(
        idempotency_key="test_idem_003_split",
        transaction_type="VENDOR_PAYMENT_WITH_FEE",
        description="Vendor payout with processing fee",
        postings=[
            PostingRequest(
                account_id=payer,
                amount=Decimal("1000.00"),
                direction=PostingDirection.DEBIT,
            ),
            PostingRequest(
                account_id=vendor,
                amount=Decimal("985.00"),
                direction=PostingDirection.CREDIT,
            ),
            PostingRequest(
                account_id=fee_account,
                amount=Decimal("15.00"),
                direction=PostingDirection.CREDIT,
            ),
        ],
    )
    assert len(entry.postings) == 3


def test_account_available_balance_property():
    """Test that available balance equals settled balance minus reserved outgoing holds."""
    acc = Account(
        account_number="AEGIS-US-12345",
        owner_id="cust_test_1",
        name="Test Account",
        account_type=AccountType.LIABILITY,
        currency="USD",
        status=AccountStatus.ACTIVE,
        settled_balance=Decimal("1000.0000"),
        reserved_outgoing=Decimal("250.0000"),
        pending_incoming=Decimal("0.0000"),
    )
    assert acc.available_balance == Decimal("750.0000")


def test_internal_transfer_distinct_accounts():
    """Test that transfer source and destination cannot be the same account."""
    acc_id = uuid.uuid4()
    with pytest.raises(ValidationError):
        InternalTransferRequest(
            idempotency_key="test_same_account_transfer",
            source_account_id=acc_id,
            destination_account_id=acc_id,
            amount=Decimal("50.00"),
        )
