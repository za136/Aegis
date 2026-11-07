"""FastAPI REST API router for Accounts & Double-Entry Ledger."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.accounts_ledger.ledger_engine import (
    AccountNotActiveError,
    InsufficientFundsError,
    InvariantViolationError,
    LedgerEngine,
)
from services.accounts_ledger.models import Account, Hold, JournalEntry
from services.accounts_ledger.schemas import (
    AccountCreateRequest,
    AccountResponse,
    HoldRequest,
    HoldResponse,
    InternalTransferRequest,
    JournalEntryRequest,
    JournalEntryResponse,
    PostingResponse,
)
from services.common.db import get_db

router = APIRouter(prefix="/ledger", tags=["Accounts & Ledger"])
engine = LedgerEngine()


@router.post(
    "/accounts",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new financial account on the ledger",
)
async def create_account(
    request: AccountCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> AccountResponse:
    account = await engine.create_account(request, db)
    return AccountResponse.model_validate(account)


@router.get(
    "/accounts/{account_id}",
    response_model=AccountResponse,
    summary="Get account balance and details by ID",
)
async def get_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> AccountResponse:
    account = await engine.get_account(account_id, db)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID {account_id} not found",
        )
    return AccountResponse.model_validate(account)


@router.get(
    "/accounts/by-number/{account_number}",
    response_model=AccountResponse,
    summary="Lookup account by account number",
)
async def get_account_by_number(
    account_number: str,
    db: AsyncSession = Depends(get_db),
) -> AccountResponse:
    stmt = select(Account).where(Account.account_number == account_number)
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_number} not found",
        )
    return AccountResponse.model_validate(account)


@router.get(
    "/accounts",
    response_model=List[AccountResponse],
    summary="List accounts by owner ID",
)
async def list_accounts_by_owner(
    owner_id: str = Query(..., description="Customer or Entity Owner ID"),
    db: AsyncSession = Depends(get_db),
) -> List[AccountResponse]:
    stmt = select(Account).where(Account.owner_id == owner_id)
    result = await db.execute(stmt)
    accounts = result.scalars().all()
    return [AccountResponse.model_validate(acc) for acc in accounts]


@router.post(
    "/entries",
    response_model=JournalEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Post an atomic double-entry journal entry with verified balancing",
)
async def post_journal_entry(
    request: JournalEntryRequest,
    db: AsyncSession = Depends(get_db),
) -> JournalEntryResponse:
    try:
        entry = await engine.post_journal_entry(request, db)
        # Reload with postings
        stmt = (
            select(JournalEntry)
            .where(JournalEntry.id == entry.id)
            .execution_options(populate_existing=True)
        )
        loaded = (await db.execute(stmt)).scalar_one()

        postings_resp = [
            PostingResponse(
                id=p.id,
                journal_entry_id=p.journal_entry_id,
                account_id=p.account_id,
                amount=p.amount,
                direction=p.direction,
                sequence=p.sequence,
            )
            for p in loaded.postings
        ]

        return JournalEntryResponse(
            id=loaded.id,
            idempotency_key=loaded.idempotency_key,
            transaction_type=loaded.transaction_type,
            description=loaded.description,
            status=loaded.status,
            posted_at=loaded.posted_at,
            postings=postings_resp,
        )

    except InsufficientFundsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AccountNotActiveError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except InvariantViolationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/transfers",
    response_model=JournalEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute an internal transfer between two customer accounts",
)
async def execute_transfer(
    request: InternalTransferRequest,
    db: AsyncSession = Depends(get_db),
) -> JournalEntryResponse:
    try:
        entry = await engine.execute_transfer(request, db)
        stmt = (
            select(JournalEntry)
            .where(JournalEntry.id == entry.id)
            .execution_options(populate_existing=True)
        )
        loaded = (await db.execute(stmt)).scalar_one()

        postings_resp = [
            PostingResponse(
                id=p.id,
                journal_entry_id=p.journal_entry_id,
                account_id=p.account_id,
                amount=p.amount,
                direction=p.direction,
                sequence=p.sequence,
            )
            for p in loaded.postings
        ]

        return JournalEntryResponse(
            id=loaded.id,
            idempotency_key=loaded.idempotency_key,
            transaction_type=loaded.transaction_type,
            description=loaded.description,
            status=loaded.status,
            posted_at=loaded.posted_at,
            postings=postings_resp,
        )

    except InsufficientFundsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AccountNotActiveError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except (InvariantViolationError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/holds",
    response_model=HoldResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a two-phase funds reservation hold",
)
async def create_hold(
    request: HoldRequest,
    db: AsyncSession = Depends(get_db),
) -> HoldResponse:
    try:
        hold = await engine.create_hold(request, db)
        return HoldResponse.model_validate(hold)
    except InsufficientFundsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AccountNotActiveError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/holds/{hold_id}/release",
    response_model=HoldResponse,
    summary="Release / void an active funds reservation hold",
)
async def release_hold(
    hold_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> HoldResponse:
    try:
        hold = await engine.release_hold(hold_id, db)
        return HoldResponse.model_validate(hold)
    except InvariantViolationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
