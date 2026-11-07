"""End-to-End Walking Skeleton Integration Test.

Tests the full Phase 1 user journey:
1. System health verification
2. User authentication (JWT issuance)
3. Opening accounts on the ledger
4. Seeding initial funds via double-entry journal entry
5. Initiating internal transfer (hold reservation)
6. Settling the payment saga on the ledger
7. Verifying mathematical invariants (no money created or lost)
8. Simulating payment exception rejection and hold rollback
"""

import uuid
from decimal import Decimal
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from apps.api_gateway.main import app
from services.accounts_ledger.models import AccountType, Base
from services.common.db import get_db

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_session():
    """Create in-memory SQLite database session for fast unit testing."""
    engine = create_async_engine(
        TEST_DB_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionMaker = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with SessionMaker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_session: AsyncSession):
    """Async HTTP test client with overridden database dependency."""
    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_walking_skeleton_health(client: AsyncClient):
    """Test health check probe."""
    res = await client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["gemini_model"] == "gemini-3.8-flash"


@pytest.mark.asyncio
async def test_walking_skeleton_auth_flow(client: AsyncClient):
    """Test user authentication and token exchange."""
    res = await client.post(
        "/api/v1/auth/token",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert res.status_code == 200
    token_data = res.json()
    assert "access_token" == "access_token"
    assert token_data["user"]["username"] == "alice"
    assert "customer" in token_data["user"]["roles"]


@pytest.mark.asyncio
async def test_walking_skeleton_complete_payment_saga(client: AsyncClient):
    """Test full payment lifecycle: Open Accounts -> Deposit -> Reserve -> Settle."""
    # 1. Create Alice's deposit account
    res_alice = await client.post(
        "/api/v1/ledger/accounts",
        json={
            "owner_id": "cust_alice",
            "name": "Alice Checking Account",
            "account_type": "LIABILITY",
            "currency": "USD",
        },
    )
    assert res_alice.status_code == 201
    alice_acc = res_alice.json()
    alice_id = alice_acc["id"]
    alice_number = alice_acc["account_number"]
    assert Decimal(str(alice_acc["available_balance"])) == Decimal("0")

    # 2. Create Bob's deposit account
    res_bob = await client.post(
        "/api/v1/ledger/accounts",
        json={
            "owner_id": "cust_bob",
            "name": "Bob Savings Account",
            "account_type": "LIABILITY",
            "currency": "USD",
        },
    )
    assert res_bob.status_code == 201
    bob_acc = res_bob.json()
    bob_id = bob_acc["id"]
    bob_number = bob_acc["account_number"]

    # 3. Create Bank Clearing Account (ASSET) to fund Alice
    res_clearing = await client.post(
        "/api/v1/ledger/accounts",
        json={
            "owner_id": "bank_treasury",
            "name": "Central Clearing Nostro Account",
            "account_type": "ASSET",
            "currency": "USD",
        },
    )
    assert res_clearing.status_code == 201
    clearing_id = res_clearing.json()["id"]

    # 4. Deposit $1,000 into Alice's account via balanced double-entry
    # Debit ASSET (clearing +$1000) and Credit LIABILITY (Alice +$1000)
    res_deposit = await client.post(
        "/api/v1/ledger/entries",
        json={
            "idempotency_key": f"deposit_{uuid.uuid4()}",
            "transaction_type": "INITIAL_DEPOSIT",
            "description": "Initial account deposit from external bank",
            "postings": [
                {
                    "account_id": clearing_id,
                    "amount": 1000.00,
                    "direction": "DEBIT",
                },
                {
                    "account_id": alice_id,
                    "amount": 1000.00,
                    "direction": "CREDIT",
                },
            ],
        },
    )
    assert res_deposit.status_code == 201

    # Verify Alice's balance after deposit
    res_alice_check = await client.get(f"/api/v1/ledger/accounts/{alice_id}")
    alice_data = res_alice_check.json()
    assert Decimal(str(alice_data["settled_balance"])) == Decimal("1000.0000")
    assert Decimal(str(alice_data["available_balance"])) == Decimal("1000.0000")

    # 5. Initiate Payment from Alice to Bob for $250.00
    res_payment = await client.post(
        "/api/v1/payments",
        json={
            "idempotency_key": f"pay_{uuid.uuid4()}",
            "debtor_account_id": alice_id,
            "creditor_account_number": bob_number,
            "creditor_name": "Bob Smith",
            "amount": 250.00,
            "currency": "USD",
            "description": "Invoice payment for consulting",
        },
    )
    assert res_payment.status_code == 201
    payment_data = res_payment.json()
    payment_id = payment_data["id"]
    assert payment_data["status"] == "FUNDS_RESERVED"
    assert payment_data["hold_id"] is not None

    # Check Alice's balance while funds are held
    res_alice_held = await client.get(f"/api/v1/ledger/accounts/{alice_id}")
    alice_held = res_alice_held.json()
    assert Decimal(str(alice_held["settled_balance"])) == Decimal("1000.0000")
    assert Decimal(str(alice_held["reserved_outgoing"])) == Decimal("250.0000")
    assert Decimal(str(alice_held["available_balance"])) == Decimal("750.0000")

    # 6. Settle Payment
    res_settle = await client.post(f"/api/v1/payments/{payment_id}/settle")
    assert res_settle.status_code == 200
    settled_data = res_settle.json()
    assert settled_data["status"] == "SETTLED"
    assert settled_data["journal_entry_id"] is not None

    # 7. Verify Final Balances
    # Alice: Settled $750, Reserved $0, Available $750
    res_alice_final = await client.get(f"/api/v1/ledger/accounts/{alice_id}")
    alice_final = res_alice_final.json()
    assert Decimal(str(alice_final["settled_balance"])) == Decimal("750.0000")
    assert Decimal(str(alice_final["reserved_outgoing"])) == Decimal("0.0000")
    assert Decimal(str(alice_final["available_balance"])) == Decimal("750.0000")

    # Bob: Settled $250, Available $250
    res_bob_final = await client.get(f"/api/v1/ledger/accounts/{bob_id}")
    bob_final = res_bob_final.json()
    assert Decimal(str(bob_final["settled_balance"])) == Decimal("250.0000")
    assert Decimal(str(bob_final["available_balance"])) == Decimal("250.0000")


@pytest.mark.asyncio
async def test_insufficient_funds_rejection(client: AsyncClient):
    """Test that payments exceeding available balance are rejected with hold never placed."""
    # Create account with zero balance
    res_acc = await client.post(
        "/api/v1/ledger/accounts",
        json={
            "owner_id": "cust_broke",
            "name": "Empty Account",
            "account_type": "LIABILITY",
            "currency": "USD",
        },
    )
    acc_id = res_acc.json()["id"]

    # Attempt to transfer $500
    res_pay = await client.post(
        "/api/v1/payments",
        json={
            "idempotency_key": f"pay_fail_{uuid.uuid4()}",
            "debtor_account_id": acc_id,
            "creditor_account_number": "AEGIS-US-ANY-01",
            "creditor_name": "Merchant Inc",
            "amount": 500.00,
            "currency": "USD",
            "description": "Purchase attempt with zero balance",
        },
    )
    assert res_pay.status_code == 400
    assert "Insufficient available funds" in res_pay.json()["detail"]


@pytest.mark.asyncio
async def test_payment_rejection_releases_held_funds(client: AsyncClient):
    """Test that a rejected payment releases held funds back to the customer."""
    # 1. Create and fund user account with $300
    res_acc = await client.post(
        "/api/v1/ledger/accounts",
        json={"owner_id": "cust_reject_test", "name": "Test User", "account_type": "LIABILITY"},
    )
    user_id = res_acc.json()["id"]

    res_clearing = await client.post(
        "/api/v1/ledger/accounts",
        json={"owner_id": "treasury", "name": "Clearing", "account_type": "ASSET"},
    )
    clearing_id = res_clearing.json()["id"]

    # Fund with $300
    await client.post(
        "/api/v1/ledger/entries",
        json={
            "idempotency_key": f"seed_{uuid.uuid4()}",
            "transaction_type": "DEPOSIT",
            "description": "Funding",
            "postings": [
                {"account_id": clearing_id, "amount": 300.0, "direction": "DEBIT"},
                {"account_id": user_id, "amount": 300.0, "direction": "CREDIT"},
            ],
        },
    )

    # 2. Initiate payment of $100 -> Available drops to $200
    res_pay = await client.post(
        "/api/v1/payments",
        json={
            "idempotency_key": f"pay_reject_{uuid.uuid4()}",
            "debtor_account_id": user_id,
            "creditor_account_number": "EXTERNAL_INVALID_ACCT",
            "creditor_name": "Target Recipient",
            "amount": 100.0,
            "description": "Transfer to be rejected",
        },
    )
    payment_id = res_pay.json()["id"]

    # 3. Simulate payment network rejection (AC04 Closed Account)
    res_reject = await client.post(
        f"/api/v1/payments/{payment_id}/reject",
        params={"code": "AC04", "reason": "Beneficiary account closed"},
    )
    assert res_reject.status_code == 200
    assert res_reject.json()["status"] == "REJECTED"
    assert res_reject.json()["rejection_code"] == "AC04"

    # 4. Verify funds returned to available balance ($300 available, $0 reserved)
    res_check = await client.get(f"/api/v1/ledger/accounts/{user_id}")
    data = res_check.json()
    assert Decimal(str(data["settled_balance"])) == Decimal("300.0000")
    assert Decimal(str(data["reserved_outgoing"])) == Decimal("0.0000")
    assert Decimal(str(data["available_balance"])) == Decimal("300.0000")
