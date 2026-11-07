"""Registered Tool Gateway Tools for Customer Support & Payment Disputes Squad."""

from decimal import Decimal
from typing import Any, Dict, Optional
from agent_platform.gateway.models import AutonomyLevel
from agent_platform.gateway.registry import register_tool
from agent_platform.squads.support_disputes.classifier import (
    RegEComplianceEngine,
    get_chargeback_network_code,
)
from agent_platform.squads.support_disputes.models import (
    DisputeClaim,
    DisputeReason,
    DisputeResolution,
    DisputeStatus,
)


DEMO_DISPUTE_CLAIMS: Dict[str, DisputeClaim] = {
    "disp_001": DisputeClaim(
        claim_id="disp_001",
        account_id="acc_usr_marcus_vance",
        transaction_id="tx_fraud_9901",
        is_consumer_account=True,
        dispute_amount=Decimal("450.00"),
        dispute_reason=DisputeReason.UNAUTHORIZED_TRANSACTION,
        customer_statement="I never authorized a $450 debit at Luxury Electronics Online on my debit card.",
        transaction_date="2026-10-10",
        statement_date="2026-10-15",
        reported_date="2026-10-18",
        card_compromise_learned_date="2026-10-17",
        status=DisputeStatus.SUBMITTED,
    ),
    "disp_002": DisputeClaim(
        claim_id="disp_002",
        account_id="acc_biz_titan_holding",
        transaction_id="tx_comm_3021",
        is_consumer_account=False,
        dispute_amount=Decimal("12000.00"),
        dispute_reason=DisputeReason.GOODS_SERVICES_NOT_RECEIVED,
        customer_statement="Commercial vendor failed to deliver server hardware.",
        transaction_date="2026-09-01",
        statement_date="2026-09-10",
        reported_date="2026-10-05",
        status=DisputeStatus.SUBMITTED,
    ),
    "disp_003": DisputeClaim(
        claim_id="disp_003",
        account_id="acc_usr_elena_rostova",
        transaction_id="tx_late_8812",
        is_consumer_account=True,
        dispute_amount=Decimal("150.00"),
        dispute_reason=DisputeReason.UNAUTHORIZED_TRANSACTION,
        customer_statement="Card charge from 5 months ago that I just noticed today.",
        transaction_date="2026-05-01",
        statement_date="2026-05-15",
        reported_date="2026-10-20",  # > 150 days later, well outside 60-day window
        status=DisputeStatus.SUBMITTED,
    ),
}

DISPUTE_RESOLUTIONS: Dict[str, DisputeResolution] = {}


@register_tool(
    name="get_dispute_transaction",
    description="Retrieve details of a disputed customer transaction and claim statements.",
    autonomy_level=AutonomyLevel.A2_ACT_WITHIN_LIMITS,
    is_write=False,
    required_squad_roles=["support_disputes", "ops_copilot"],
)
def get_dispute_transaction(claim_id: str) -> Dict[str, Any]:
    """Fetch dispute claim details."""
    claim = DEMO_DISPUTE_CLAIMS.get(claim_id)
    if not claim:
        return {"error": f"Dispute claim '{claim_id}' not found."}
    return claim.model_dump(mode="json")


@register_tool(
    name="evaluate_reg_e_compliance",
    description="Evaluate a customer dispute claim against CFPB Regulation E (12 CFR § 1005) statutory rules.",
    autonomy_level=AutonomyLevel.A2_ACT_WITHIN_LIMITS,
    is_write=False,
    required_squad_roles=["support_disputes", "ops_copilot"],
)
def evaluate_reg_e_compliance(claim_id: str) -> Dict[str, Any]:
    """Execute the Reg E compliance evaluation engine."""
    claim = DEMO_DISPUTE_CLAIMS.get(claim_id)
    if not claim:
        return {"error": f"Dispute claim '{claim_id}' not found."}

    assessment = RegEComplianceEngine.assess_reg_e(claim)
    cb_code = get_chargeback_network_code(claim.dispute_reason)

    return {
        "assessment": assessment.model_dump(mode="json"),
        "chargeback_network_code": cb_code,
    }


@register_tool(
    name="issue_provisional_credit",
    description="Issue temporary provisional credit to consumer account pending formal dispute investigation under 12 CFR § 1005.11(c). Requires A1 supervisor approval.",
    autonomy_level=AutonomyLevel.A1_ACT_WITH_APPROVAL,
    is_write=True,
    required_squad_roles=["support_disputes"],
)
def issue_provisional_credit(claim_id: str, credit_amount: str, rationale: str) -> Dict[str, Any]:
    """Issue provisional credit to consumer account."""
    claim = DEMO_DISPUTE_CLAIMS.get(claim_id)
    if not claim:
        return {"error": f"Dispute claim '{claim_id}' not found."}

    claim.status = DisputeStatus.PROVISIONAL_CREDIT_GRANTED
    return {
        "claim_id": claim_id,
        "status": "PROVISIONAL_CREDIT_ISSUED",
        "account_id": claim.account_id,
        "credited_amount": credit_amount,
        "regulatory_statute": "12 CFR § 1005.11(c)",
        "rationale": rationale,
    }


@register_tool(
    name="submit_dispute_resolution",
    description="Finalize dispute investigation disposition (chargeback representation or closure). Requires A1 authorization.",
    autonomy_level=AutonomyLevel.A1_ACT_WITH_APPROVAL,
    is_write=True,
    required_squad_roles=["support_disputes"],
)
def submit_dispute_resolution(
    claim_id: str,
    status: str,
    final_credit_amount: str,
    investigation_summary: str,
) -> Dict[str, Any]:
    """Finalize dispute resolution disposition."""
    claim = DEMO_DISPUTE_CLAIMS.get(claim_id)
    if not claim:
        return {"error": f"Dispute claim '{claim_id}' not found."}

    resolution = DisputeResolution(
        claim_id=claim_id,
        status=DisputeStatus(status),
        final_credit_amount=Decimal(final_credit_amount),
        investigation_summary=investigation_summary,
        chargeback_reason_code=get_chargeback_network_code(claim.dispute_reason),
    )
    DISPUTE_RESOLUTIONS[claim_id] = resolution
    claim.status = DisputeStatus(status)

    return resolution.model_dump(mode="json")
