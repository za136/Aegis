"""Comprehensive Unit and Integration Tests for Phase 7 Stretch Squads:
- B2B Invoice Reconciliation Squad
- Customer Support & Payment Disputes Squad (Reg E Compliance)
- Operations Copilot Squad
- Bulk Payment Batch Simulator & Processor (ISO 20022 pacs.008)
"""

from decimal import Decimal
import pytest

from agent_platform.gateway.approvals import approval_inbox
from agent_platform.squads.ops_copilot.copilot import ops_copilot
from agent_platform.squads.ops_copilot.models import CopilotQueryRequest
from agent_platform.squads.reconciliation.agent import reconciliation_agent
from agent_platform.squads.reconciliation.matcher import ReconciliationEngine
from agent_platform.squads.reconciliation.models import (
    Invoice,
    InvoiceStatus,
    LedgerPostingItem,
    MatchType,
)
from agent_platform.squads.reconciliation.tools import apply_reconciliation_batch
from agent_platform.squads.support_disputes.agent import disputes_agent
from agent_platform.squads.support_disputes.classifier import RegEComplianceEngine
from agent_platform.squads.support_disputes.models import (
    DisputeClaim,
    DisputeReason,
    DisputeStatus,
)
from simulators.bulk_payments import (
    BulkPaymentBatch,
    BulkPaymentItem,
    bulk_processor,
)


# =====================================================================
# 1. B2B INVOICE RECONCILIATION SQUAD TESTS
# =====================================================================

def test_reconciliation_exact_and_fuzzy_matching():
    """Verify exact 1-to-1 matching and fuzzy reference matching."""
    invoices = [
        Invoice(
            invoice_id="inv_test_1",
            vendor_id="vend_1",
            customer_id="cust_1",
            invoice_number="INV-2026-101",
            amount=Decimal("5000.00"),
            issue_date="2026-10-01",
            due_date="2026-10-31",
        ),
        Invoice(
            invoice_id="inv_test_2",
            vendor_id="vend_2",
            customer_id="cust_2",
            invoice_number="REF-9923",
            amount=Decimal("1200.00"),
            issue_date="2026-10-05",
            due_date="2026-11-05",
        ),
    ]

    postings = [
        LedgerPostingItem(
            posting_id="post_test_1",
            account_id="acc_vend_1",
            amount=Decimal("5000.00"),
            direction="CREDIT",
            narrative="WIRE FROM CUST 1 FOR INV-2026-101 FULL",
        ),
        LedgerPostingItem(
            posting_id="post_test_2",
            account_id="acc_vend_2",
            amount=Decimal("1200.00"),
            direction="CREDIT",
            narrative="ACH CR CUST2 REF 9923 OCT INV",  # Fuzzy without hyphen
        ),
    ]

    batch = ReconciliationEngine.run_reconciliation(postings, invoices)
    assert len(batch.matches) == 2
    assert batch.total_matched_volume == Decimal("6200.00")

    exact_match = next(m for m in batch.matches if m.matched_invoice_ids == ["inv_test_1"])
    assert exact_match.match_type == MatchType.EXACT_ONE_TO_ONE
    assert exact_match.confidence_score == 1.0

    fuzzy_match = next(m for m in batch.matches if m.matched_invoice_ids == ["inv_test_2"])
    assert fuzzy_match.match_type in [MatchType.EXACT_ONE_TO_ONE, MatchType.FUZZY_REFERENCE]
    assert fuzzy_match.confidence_score >= 0.90


def test_reconciliation_two_to_one_split_payment():
    """Verify 2-to-1 split payment matching where 1 payment settles 2 invoices."""
    invoices = [
        Invoice(
            invoice_id="inv_split_a",
            vendor_id="vend_acme",
            customer_id="cust_retail",
            invoice_number="INV-A100",
            amount=Decimal("3000.00"),
            issue_date="2026-10-01",
            due_date="2026-10-31",
        ),
        Invoice(
            invoice_id="inv_split_b",
            vendor_id="vend_acme",
            customer_id="cust_retail",
            invoice_number="INV-B200",
            amount=Decimal("4500.00"),
            issue_date="2026-10-05",
            due_date="2026-11-05",
        ),
    ]

    postings = [
        LedgerPostingItem(
            posting_id="post_split_1",
            account_id="acc_vend_acme",
            amount=Decimal("7500.00"),  # 3000 + 4500
            direction="CREDIT",
            narrative="REMITTANCE COMBINED BATCH INV-A100 AND INV-B200",
        ),
    ]

    batch = ReconciliationEngine.run_reconciliation(postings, invoices)
    assert len(batch.matches) == 1
    match = batch.matches[0]
    assert match.match_type == MatchType.SPLIT_PAYMENT_COMBINED
    assert set(match.matched_invoice_ids) == {"inv_split_a", "inv_split_b"}
    assert match.total_posting_amount == Decimal("7500.00")
    assert match.total_invoice_amount == Decimal("7500.00")


@pytest.mark.asyncio
async def test_reconciliation_agent_execution_and_a1_ticket():
    """Verify the autonomous reconciliation agent runs and generates an A1 review ticket."""
    report = await reconciliation_agent.run(auto_submit_approval=True)
    assert report.batch_id.startswith("batch_")
    assert report.match_count > 0
    assert report.status in ["PENDING_ACCOUNTING_APPROVAL", "APPLIED", "PROPOSED"]
    if report.approval_ticket_id:
        ticket = await approval_inbox.get_ticket(report.approval_ticket_id)
        assert ticket is not None
        assert ticket.squad_name == "reconciliation"
        assert ticket.tool_name == "apply_reconciliation_batch"


# =====================================================================
# 2. CUSTOMER SUPPORT & PAYMENT DISPUTES SQUAD (REG E) TESTS
# =====================================================================

def test_reg_e_eligible_consumer_claim():
    """Verify timely consumer unauthorized transaction qualifies for Reg E with $50 liability."""
    claim = DisputeClaim(
        claim_id="disp_test_eligible",
        account_id="acc_user_1",
        transaction_id="tx_1",
        is_consumer_account=True,
        dispute_amount=Decimal("500.00"),
        dispute_reason=DisputeReason.UNAUTHORIZED_TRANSACTION,
        customer_statement="Unauthorized debit on my debit card.",
        transaction_date="2026-10-01",
        statement_date="2026-10-05",
        reported_date="2026-10-08",
        card_compromise_learned_date="2026-10-07",  # Reported within 1 day of learning
    )

    assessment = RegEComplianceEngine.assess_reg_e(claim)
    assert assessment.is_reg_e_eligible is True
    assert assessment.within_60_day_window is True
    assert assessment.consumer_max_liability == Decimal("50.00")
    assert assessment.provisional_credit_mandated is True


def test_reg_e_ineligible_commercial_account():
    """Verify commercial/business accounts are strictly exempt from Regulation E."""
    claim = DisputeClaim(
        claim_id="disp_test_comm",
        account_id="acc_biz_1",
        transaction_id="tx_2",
        is_consumer_account=False,  # Commercial account
        dispute_amount=Decimal("5000.00"),
        dispute_reason=DisputeReason.UNAUTHORIZED_TRANSACTION,
        customer_statement="Commercial wire dispute.",
        transaction_date="2026-10-01",
        statement_date="2026-10-05",
        reported_date="2026-10-10",
    )

    assessment = RegEComplianceEngine.assess_reg_e(claim)
    assert assessment.is_reg_e_eligible is False
    assert "Commercial / business accounts are exempt" in assessment.reasoning


def test_reg_e_expired_notice_over_60_days():
    """Verify claims reported over 60 days after statement lose statutory Reg E mandate."""
    claim = DisputeClaim(
        claim_id="disp_test_expired",
        account_id="acc_user_2",
        transaction_id="tx_3",
        is_consumer_account=True,
        dispute_amount=Decimal("300.00"),
        dispute_reason=DisputeReason.UNAUTHORIZED_TRANSACTION,
        customer_statement="Disputing an unauthorized charge from 4 months ago.",
        transaction_date="2026-05-01",
        statement_date="2026-05-10",
        reported_date="2026-09-15",  # > 120 days later
    )

    assessment = RegEComplianceEngine.assess_reg_e(claim)
    assert assessment.is_reg_e_eligible is False
    assert assessment.within_60_day_window is False
    assert "outside the statutory 60-day notice window" in assessment.reasoning


@pytest.mark.asyncio
async def test_disputes_agent_end_to_end_flow():
    """Verify the Disputes Agent assesses disp_001 and issues an A1 ticket for provisional credit."""
    report = await disputes_agent.run("disp_001")
    assert report.claim_id == "disp_001"
    assert report.is_reg_e_eligible is True
    assert report.provisional_credit_amount == "450.00"
    assert report.status in ["PENDING_SUPERVISOR_APPROVAL", "PROVISIONAL_CREDIT_GRANTED"]
    if report.approval_ticket_id:
        ticket = await approval_inbox.get_ticket(report.approval_ticket_id)
        assert ticket.squad_name == "support_disputes"
        assert ticket.tool_name == "issue_provisional_credit"


# =====================================================================
# 3. OPERATIONS COPILOT SQUAD TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_ops_copilot_ledger_query():
    """Verify Copilot answers ledger query with grounded citations and navigation actions."""
    query = CopilotQueryRequest(query="What is our total customer deposit balance and pending holds?")
    answer = await ops_copilot.answer(query)
    assert "deposit" in answer.answer_markdown.lower() or "ledger" in answer.answer_markdown.lower()
    assert len(answer.citations) >= 2
    assert any("[CITE:ledger_summary" in c.citation_tag for c in answer.citations)
    assert any(a.action_type == "NAVIGATE" for a in answer.suggested_actions)


@pytest.mark.asyncio
async def test_ops_copilot_approvals_query():
    """Verify Copilot queries approval queue and returns ticket count citation."""
    query = CopilotQueryRequest(query="How many pending approval tickets do we have in the inbox?")
    answer = await ops_copilot.answer(query)
    assert len(answer.citations) >= 1
    assert any("[CITE:approval_inbox" in c.citation_tag for c in answer.citations)


# =====================================================================
# 4. BULK PAYMENT PROCESSOR (ISO 20022 PACS.008) TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_bulk_payment_batch_processor():
    """Verify bulk payment simulation, ISO 20022 XML generation, and payment saga settlement."""
    items = [
        BulkPaymentItem(
            end_to_end_id="PAYROLL-001",
            debtor_account_id="acc_biz_acme_corp",
            creditor_account_id="acc_usr_alice_smith",
            creditor_name="Alice Smith",
            amount=Decimal("4500.00"),
            remittance_info="October 2026 Salary",
        ),
        BulkPaymentItem(
            end_to_end_id="PAYROLL-002",
            debtor_account_id="acc_biz_acme_corp",
            creditor_account_id="acc_usr_bob_jones",
            creditor_name="Bob Jones",
            amount=Decimal("5200.00"),
            remittance_info="October 2026 Salary",
        ),
    ]

    batch = BulkPaymentBatch(
        batch_id="batch_payroll_2026_10",
        batch_reference="OCT-PAYROLL-01",
        debtor_company_id="Acme Corporation Inc.",
        total_instructions=2,
        total_batch_volume=Decimal("9700.00"),
        items=items,
    )

    # 1. Test ISO 20022 XML generation
    xml_output = bulk_processor.generate_iso20022_pacs008_xml(batch)
    assert 'xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.10"' in xml_output
    assert "<NbOfTxs>2</NbOfTxs>" in xml_output
    assert "<TtlIntrBkSttlmAmt Ccy=\"USD\">9700.00</TtlIntrBkSttlmAmt>" in xml_output
    assert "<EndToEndId>PAYROLL-001</EndToEndId>" in xml_output
    assert "<EndToEndId>PAYROLL-002</EndToEndId>" in xml_output

    # 2. Process batch through saga
    summary = await bulk_processor.process_batch(batch)
    assert summary.batch_id == "batch_payroll_2026_10"
    assert summary.total_processed == 2
    assert summary.settled_count == 2
    assert summary.failed_count == 0
    assert summary.total_settled_volume == "9700.00"
    assert summary.execution_duration_ms > 0
