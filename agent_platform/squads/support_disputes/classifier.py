"""Regulation E (12 CFR Part 1005) Compliance and Dispute Classification Engine."""

from datetime import date
from decimal import Decimal
from typing import Optional
from agent_platform.squads.support_disputes.models import (
    DisputeClaim,
    DisputeReason,
    RegEAssessment,
)


CHARGEBACK_REASON_CODES = {
    DisputeReason.UNAUTHORIZED_TRANSACTION: "VISA_10_4_FRAUD_UNAUTHORIZED",
    DisputeReason.GOODS_SERVICES_NOT_RECEIVED: "VISA_13_1_MERCHANDISE_NOT_RECEIVED",
    DisputeReason.DEFECTIVE_OR_NOT_AS_DESCRIBED: "VISA_13_3_NOT_AS_DESCRIBED",
    DisputeReason.DUPLICATE_PROCESSING: "VISA_12_6_DUPLICATE_PROCESSING",
    DisputeReason.INCORRECT_AMOUNT: "VISA_12_5_INCORRECT_TRANSACTION_AMOUNT",
}


class RegEComplianceEngine:
    """Evaluates electronic fund transfer disputes against Consumer Financial Protection Bureau (CFPB) Regulation E rules."""

    @staticmethod
    def assess_reg_e(claim: DisputeClaim) -> RegEAssessment:
        """Evaluate statutory Reg E eligibility, 60-day notice window, consumer liability, and provisional credit requirements."""
        # Rule 1: Consumer Account check (12 CFR § 1005.2(b))
        if not claim.is_consumer_account:
            return RegEAssessment(
                claim_id=claim.claim_id,
                is_reg_e_eligible=False,
                within_60_day_window=False,
                days_since_statement=0,
                days_to_notice=0,
                consumer_max_liability=claim.dispute_amount,
                provisional_credit_mandated=False,
                reasoning="Claim rejected under Regulation E: Commercial / business accounts are exempt from 12 C.F.R. § 1005 consumer protections.",
            )

        # Rule 2: 60-day notice window from periodic statement (12 CFR § 1005.11(b)(1)(i))
        days_since_statement = (claim.reported_date - claim.statement_date).days
        within_60_days = days_since_statement <= 60

        if not within_60_days:
            return RegEAssessment(
                claim_id=claim.claim_id,
                is_reg_e_eligible=False,
                within_60_day_window=False,
                days_since_statement=days_since_statement,
                days_to_notice=days_since_statement,
                consumer_max_liability=claim.dispute_amount,
                provisional_credit_mandated=False,
                reasoning=f"Claim is outside the statutory 60-day notice window ({days_since_statement} days since periodic statement). Statutory Reg E investigation mandate does not apply.",
            )

        # Rule 3: Consumer Liability Tier calculation (12 CFR § 1005.6)
        # Default tier: $50 liability if reported within 2 business days of learning of card compromise
        max_liability = Decimal("50.00")
        if claim.card_compromise_learned_date:
            days_to_notice = (claim.reported_date - claim.card_compromise_learned_date).days
            if days_to_notice > 2:
                # Reported after 2 business days: Liability capped at $500
                max_liability = min(Decimal("500.00"), claim.dispute_amount)
            else:
                max_liability = min(Decimal("50.00"), claim.dispute_amount)
        else:
            days_to_notice = days_since_statement
            max_liability = min(Decimal("50.00"), claim.dispute_amount)

        # Rule 4: Mandatory Provisional Credit provision (12 CFR § 1005.11(c))
        # If investigation exceeds 10 business days, provisional credit for full disputed amount is required
        provisional_credit_mandated = True
        eligible_credit = max(Decimal("0.00"), claim.dispute_amount - max_liability)

        reasoning = (
            f"Eligible under 12 CFR § 1005: Timely notice received {days_since_statement} days after statement. "
            f"Consumer maximum statutory liability is capped at ${max_liability}. "
            f"Mandatory provisional credit of ${claim.dispute_amount} must be issued if investigation exceeds 10 business days."
        )

        return RegEAssessment(
            claim_id=claim.claim_id,
            is_reg_e_eligible=True,
            within_60_day_window=True,
            days_since_statement=days_since_statement,
            days_to_notice=days_to_notice,
            consumer_max_liability=max_liability,
            provisional_credit_mandated=provisional_credit_mandated,
            provisional_credit_deadline_days=10,
            reasoning=reasoning,
        )


def get_chargeback_network_code(reason: DisputeReason) -> str:
    """Return the corresponding card network chargeback reason code."""
    return CHARGEBACK_REASON_CODES.get(reason, "VISA_10_4_FRAUD_UNAUTHORIZED")
