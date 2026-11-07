"""FastAPI REST API router for Payments and Lifecycle Saga."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.common.db import get_db
from services.payments.models import Payment, PaymentStatus
from services.payments.saga import PaymentSagaCoordinator, PaymentSagaError
from services.payments.schemas import PaymentCreateRequest, PaymentResponse

router = APIRouter(prefix="/payments", tags=["Payments"])
saga = PaymentSagaCoordinator()


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate a payment instruction (runs validation & ledger funds reservation)",
)
async def initiate_payment(
    request: PaymentCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> PaymentResponse:
    try:
        payment = await saga.initiate_payment(request, db)
        return PaymentResponse.model_validate(payment)
    except PaymentSagaError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    summary="Get payment details and state machine history",
)
async def get_payment(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> PaymentResponse:
    stmt = select(Payment).where(Payment.id == payment_id)
    payment = (await db.execute(stmt)).scalar_one_or_none()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment {payment_id} not found",
        )
    return PaymentResponse.model_validate(payment)


@router.post(
    "/{payment_id}/settle",
    response_model=PaymentResponse,
    summary="Settle internal payment on ledger and capture hold",
)
async def settle_payment(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> PaymentResponse:
    try:
        payment = await saga.settle_internal_payment(payment_id, db)
        return PaymentResponse.model_validate(payment)
    except PaymentSagaError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{payment_id}/reject",
    response_model=PaymentResponse,
    summary="Simulate payment rejection and release reserved funds (for Payment Repair squad)",
)
async def reject_payment(
    payment_id: uuid.UUID,
    code: str = Query("AC04", description="ISO 20022 rejection code (e.g. AC04: Closed Account)"),
    reason: str = Query("Account closed or invalid account number"),
    db: AsyncSession = Depends(get_db),
) -> PaymentResponse:
    try:
        payment = await saga.fail_or_reject_payment(payment_id, code, reason, db)
        return PaymentResponse.model_validate(payment)
    except PaymentSagaError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "",
    response_model=List[PaymentResponse],
    summary="List payments filtered by debtor account or status",
)
async def list_payments(
    debtor_account_id: Optional[uuid.UUID] = Query(None),
    payment_status: Optional[PaymentStatus] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[PaymentResponse]:
    stmt = select(Payment).order_by(Payment.created_at.desc()).limit(limit)
    if debtor_account_id:
        stmt = stmt.where(Payment.debtor_account_id == debtor_account_id)
    if payment_status:
        stmt = stmt.where(Payment.status == payment_status)

    result = await db.execute(stmt)
    payments = result.scalars().all()
    return [PaymentResponse.model_validate(p) for p in payments]
