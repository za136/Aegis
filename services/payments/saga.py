"""Payment Lifecycle Saga Coordinator enforcing two-phase ledger reservation and settlement."""

import uuid
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.accounts_ledger.ledger_engine import (
    InsufficientFundsError,
    LedgerEngine,
)
from services.accounts_ledger.models import Account, AccountStatus
from services.accounts_ledger.schemas import (
    HoldRequest,
    InternalTransferRequest,
)
from services.payments.models import Payment, PaymentStatus
from services.payments.schemas import PaymentCreateRequest


class PaymentSagaError(Exception):
    """Base exception for payment saga errors."""
    pass


class PaymentSagaCoordinator:
    """Orchestrates payment lifecycle transitions across ledger reservation and settlement."""

    def __init__(self, ledger_engine: Optional[LedgerEngine] = None):
        self.ledger = ledger_engine or LedgerEngine()

    async def initiate_payment(
        self, request: PaymentCreateRequest, db: AsyncSession
    ) -> Payment:
        """Step 1 to 5: Create instruction, validate, reserve funds on ledger."""
        # Check idempotency
        stmt = select(Payment).where(Payment.idempotency_key == request.idempotency_key)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing

        # Fetch debtor account
        debtor = await self.ledger.get_account(request.debtor_account_id, db)
        if not debtor:
            raise PaymentSagaError(f"Debtor account {request.debtor_account_id} not found.")

        if debtor.status != AccountStatus.ACTIVE:
            raise PaymentSagaError(f"Debtor account is {debtor.status.value}.")

        # Lookup if creditor is an internal account
        stmt_cred = select(Account).where(Account.account_number == request.creditor_account_number)
        creditor = (await db.execute(stmt_cred)).scalar_one_or_none()

        # Step 1: Create payment instruction
        payment = Payment(
            idempotency_key=request.idempotency_key,
            debtor_account_id=debtor.id,
            creditor_account_id=creditor.id if creditor else None,
            creditor_account_number=request.creditor_account_number,
            creditor_name=request.creditor_name,
            amount=request.amount,
            currency=request.currency.upper(),
            description=request.description,
            status=PaymentStatus.CREATED,
            state_history=[],
        )
        payment.transition_to(PaymentStatus.CREATED, "Payment initiated by customer")
        db.add(payment)
        await db.flush()

        # Step 2: Validate format and accounts
        payment.transition_to(PaymentStatus.VALIDATED, "Basic format and debtor check passed")

        # Step 3: Risk screening placeholder (rules engine / Aegis squad hook)
        payment.transition_to(PaymentStatus.SCREENING, "Automated sanctions & AML rules check")

        # Step 4: Funds Reservation on Ledger (Two-phase hold)
        try:
            hold = await self.ledger.create_hold(
                HoldRequest(
                    account_id=debtor.id,
                    amount=request.amount,
                    currency=request.currency,
                    reference=f"PAYMENT_HOLD_{payment.id}",
                ),
                db,
            )
            payment.hold_id = hold.id
            payment.transition_to(
                PaymentStatus.FUNDS_RESERVED,
                f"Funds held on ledger (Hold ID: {hold.id})"
            )
            await db.flush()
        except InsufficientFundsError as e:
            payment.transition_to(PaymentStatus.FAILED, f"Insufficient funds: {str(e)}")
            payment.rejection_code = "AM04"  # ISO 20022 Insufficient Funds
            payment.rejection_reason = str(e)
            await db.flush()
            raise

        return payment

    async def settle_internal_payment(
        self, payment_id: uuid.UUID, db: AsyncSession
    ) -> Payment:
        """Step 6 & 7: Settle internal payment on ledger and release hold."""
        stmt = select(Payment).where(Payment.id == payment_id).with_for_update()
        payment = (await db.execute(stmt)).scalar_one_or_none()
        if not payment:
            raise PaymentSagaError(f"Payment {payment_id} not found.")

        if payment.status != PaymentStatus.FUNDS_RESERVED:
            raise PaymentSagaError(
                f"Cannot settle payment with status {payment.status.value}. Must be FUNDS_RESERVED."
            )

        if not payment.creditor_account_id:
            raise PaymentSagaError("Cannot settle internally: Creditor account is external.")

        payment.transition_to(PaymentStatus.SUBMITTED, "Instruction submitted for settlement")

        # 1. Release the reservation hold so settled balance can be moved
        if payment.hold_id:
            await self.ledger.release_hold(payment.hold_id, db)
            payment.hold_id = None

        # 2. Execute balanced transfer on ledger
        journal_entry = await self.ledger.execute_transfer(
            InternalTransferRequest(
                idempotency_key=f"SETTLE_{payment.idempotency_key}",
                source_account_id=payment.debtor_account_id,
                destination_account_id=payment.creditor_account_id,
                amount=payment.amount,
                currency=payment.currency,
                description=f"Settlement: {payment.description}",
            ),
            db,
        )

        payment.journal_entry_id = journal_entry.id
        payment.transition_to(
            PaymentStatus.SETTLED,
            f"Transfer posted to ledger (Journal Entry ID: {journal_entry.id})"
        )
        await db.flush()
        return payment

    async def fail_or_reject_payment(
        self,
        payment_id: uuid.UUID,
        rejection_code: str,
        rejection_reason: str,
        db: AsyncSession,
    ) -> Payment:
        """Reject a payment and release any reserved funds back to debtor."""
        stmt = select(Payment).where(Payment.id == payment_id).with_for_update()
        payment = (await db.execute(stmt)).scalar_one_or_none()
        if not payment:
            raise PaymentSagaError(f"Payment {payment_id} not found.")

        # Release hold if active
        if payment.hold_id:
            try:
                await self.ledger.release_hold(payment.hold_id, db)
            except Exception:
                pass
            payment.hold_id = None

        payment.rejection_code = rejection_code
        payment.rejection_reason = rejection_reason
        payment.transition_to(
            PaymentStatus.REJECTED,
            f"Payment rejected [{rejection_code}]: {rejection_reason}"
        )
        await db.flush()
        return payment

    async def execute_payment(self, instruction: Any) -> Any:
        """Execute simulated payment instruction for batch processing."""
        if hasattr(instruction, "status"):
            instruction.status = PaymentStatus.SETTLED
        return instruction


# Export singleton instance for simulator and coordinator usage
payment_saga = PaymentSagaCoordinator()
