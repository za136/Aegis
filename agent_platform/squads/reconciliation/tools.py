"""Registered Tool Gateway Tools for B2B Invoice and Remittance Reconciliation."""

from decimal import Decimal
from typing import Any, Dict, List
from agent_platform.gateway.models import AutonomyLevel
from agent_platform.gateway.registry import register_tool
from agent_platform.squads.reconciliation.matcher import ReconciliationEngine
from agent_platform.squads.reconciliation.models import (
    Invoice,
    InvoiceStatus,
    LedgerPostingItem,
    ReconciliationBatch,
)


# In-memory mock store for invoices and ledger postings
DEMO_INVOICES: Dict[str, Invoice] = {
    "inv_001": Invoice(
        invoice_id="inv_001",
        vendor_id="vend_acme_corp",
        customer_id="cust_apex_retail",
        invoice_number="INV-2026-9001",
        amount=Decimal("12500.00"),
        issue_date="2026-10-01",
        due_date="2026-10-31",
        status=InvoiceStatus.UNPAID,
    ),
    "inv_002": Invoice(
        invoice_id="inv_002",
        vendor_id="vend_acme_corp",
        customer_id="cust_apex_retail",
        invoice_number="INV-2026-9002",
        amount=Decimal("7500.00"),
        issue_date="2026-10-05",
        due_date="2026-11-05",
        status=InvoiceStatus.UNPAID,
    ),
    "inv_003": Invoice(
        invoice_id="inv_003",
        vendor_id="vend_logistics_co",
        customer_id="cust_zenith_mfg",
        invoice_number="INV-8834",
        amount=Decimal("4200.50"),
        issue_date="2026-10-15",
        due_date="2026-11-15",
        status=InvoiceStatus.UNPAID,
    ),
    "inv_004": Invoice(
        invoice_id="inv_004",
        vendor_id="vend_cloud_saas",
        customer_id="cust_solaris_tech",
        invoice_number="SAAS-5501",
        amount=Decimal("1890.00"),
        issue_date="2026-10-20",
        due_date="2026-11-20",
        status=InvoiceStatus.UNPAID,
    ),
}

DEMO_POSTINGS: Dict[str, LedgerPostingItem] = {
    "post_001": LedgerPostingItem(
        posting_id="post_001",
        account_id="acc_vend_acme_corp",
        amount=Decimal("20000.00"),
        direction="CREDIT",
        narrative="WIRE INBOUND FROM APEX RETAIL COMBINED INV-2026-9001 & INV-2026-9002",
        reconciled=False,
    ),
    "post_002": LedgerPostingItem(
        posting_id="post_002",
        account_id="acc_vend_logistics_co",
        amount=Decimal("4200.50"),
        direction="CREDIT",
        narrative="ACH CR FROM ZENITH MFG REF INV-8834 OCT SERVICES",
        reconciled=False,
    ),
    "post_003": LedgerPostingItem(
        posting_id="post_003",
        account_id="acc_vend_cloud_saas",
        amount=Decimal("1000.00"),
        direction="CREDIT",
        narrative="PARTIAL SETTLEMENT SAAS-5501 SOLARIS TECH",
        reconciled=False,
    ),
}

BATCH_STORE: Dict[str, ReconciliationBatch] = {}


@register_tool(
    name="fetch_unreconciled_postings",
    description="Retrieve all unreconciled incoming credit postings from the double-entry ledger.",
    autonomy_level=AutonomyLevel.A2_ACT_WITHIN_LIMITS,
    is_write=False,
    required_squad_roles=["reconciliation", "ops_copilot"],
)
def fetch_unreconciled_postings(account_id: str = "") -> List[Dict[str, Any]]:
    """Retrieve credit postings requiring reconciliation."""
    if account_id:
        items = [p for p in DEMO_POSTINGS.values() if p.account_id == account_id and not p.reconciled]
    else:
        items = [p for p in DEMO_POSTINGS.values() if not p.reconciled]
    return [p.model_dump(mode="json") for p in items]


@register_tool(
    name="fetch_pending_invoices",
    description="Retrieve all outstanding, unpaid, or partially paid invoices from accounts receivable.",
    autonomy_level=AutonomyLevel.A2_ACT_WITHIN_LIMITS,
    is_write=False,
    required_squad_roles=["reconciliation", "ops_copilot"],
)
def fetch_pending_invoices(customer_id: str = "") -> List[Dict[str, Any]]:
    """Retrieve unpaid invoices eligible for reconciliation."""
    if customer_id:
        items = [inv for inv in DEMO_INVOICES.values() if inv.customer_id == customer_id and inv.status != InvoiceStatus.PAID]
    else:
        items = [inv for inv in DEMO_INVOICES.values() if inv.status != InvoiceStatus.PAID]
    return [inv.model_dump(mode="json") for inv in items]


@register_tool(
    name="propose_reconciliation_batch",
    description="Execute the multi-pass reconciliation matcher over unreconciled postings and pending invoices.",
    autonomy_level=AutonomyLevel.A2_ACT_WITHIN_LIMITS,
    is_write=False,
    required_squad_roles=["reconciliation"],
)
def propose_reconciliation_batch() -> Dict[str, Any]:
    """Execute the matching engine and generate a draft reconciliation batch."""
    batch = ReconciliationEngine.run_reconciliation(
        postings=list(DEMO_POSTINGS.values()),
        invoices=list(DEMO_INVOICES.values()),
    )
    BATCH_STORE[batch.batch_id] = batch
    return batch.model_dump(mode="json")


@register_tool(
    name="apply_reconciliation_batch",
    description="Apply an approved reconciliation batch to mark postings as reconciled and update invoice payment statuses. Requires A1 accounting authorization.",
    autonomy_level=AutonomyLevel.A1_ACT_WITH_APPROVAL,
    is_write=True,
    required_squad_roles=["reconciliation"],
)
def apply_reconciliation_batch(batch_id: str) -> Dict[str, Any]:
    """Apply approved reconciliation matches to mark records reconciled."""
    batch = BATCH_STORE.get(batch_id)
    if not batch:
        return {"error": f"Reconciliation batch '{batch_id}' not found."}

    applied_matches = 0
    for match in batch.matches:
        # Mark postings reconciled
        for p_id in match.matched_posting_ids:
            if p_id in DEMO_POSTINGS:
                DEMO_POSTINGS[p_id].reconciled = True
        # Mark invoices paid or partially paid
        for inv_id in match.matched_invoice_ids:
            if inv_id in DEMO_INVOICES:
                inv = DEMO_INVOICES[inv_id]
                if match.match_type.value == "PARTIAL_PAYMENT":
                    inv.status = InvoiceStatus.PARTIALLY_PAID
                    inv.paid_amount += match.total_posting_amount
                else:
                    inv.status = InvoiceStatus.PAID
                    inv.paid_amount = inv.amount
        match.approved = True
        applied_matches += 1

    batch.status = "APPLIED"
    return {
        "batch_id": batch.batch_id,
        "status": "APPLIED",
        "matches_applied": applied_matches,
        "total_volume_reconciled": str(batch.total_matched_volume),
    }
