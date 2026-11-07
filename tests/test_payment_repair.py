"""Integration tests for Payment Exception Repair Squad with Gemini 3.8 Flash & Tool Gateway."""

import pytest
from agent_platform.gateway.approvals import approval_inbox
from agent_platform.gateway.models import TicketStatus
from agent_platform.squads.payment_repair.agent import PaymentRepairAgent
from agent_platform.squads.payment_repair.diagnostics import diagnose_rejection_code


def test_diagnostics_rules():
    """Verify diagnostic rules for standard ISO 20022 exception codes."""
    rule_ac04 = diagnose_rejection_code("AC04")
    assert rule_ac04 is not None
    assert rule_ac04.repairable is True
    assert "Account Closed" in rule_ac04.meaning

    rule_am04 = diagnose_rejection_code("AM04")
    assert rule_am04 is not None
    assert rule_am04.repairable is False  # Invariant violation cannot be bypassed

    rule_be05 = diagnose_rejection_code("BE05")
    assert rule_be05 is not None
    assert rule_be05.repairable is True


@pytest.mark.asyncio
async def test_payment_repair_agent_ac04_investigation():
    """Verify agent investigates AC04 rejection, consults directory, and submits A1 repair proposal."""
    agent = PaymentRepairAgent(model_name="gemini-3.8-flash")
    result = await agent.run(payment_id="pmt_ex_101")

    assert result.payment_id == "pmt_ex_101"
    assert result.rejection_code == "AC04"
    assert result.is_repairable is True
    assert result.proposed_account_number == "US33WELL9988222"
    assert result.confidence >= 0.95
    assert result.status == "PENDING_APPROVAL"
    assert result.approval_ticket_id is not None

    # Verify that the action generated a pending ticket in the approval inbox
    ticket = await approval_inbox.get_ticket(result.approval_ticket_id)
    assert ticket is not None
    assert ticket.status == TicketStatus.PENDING
    assert ticket.squad_name == "payment_repair"
    assert "AC04" in ticket.reasoning

    # Verify human approval executes the repair
    approved = await approval_inbox.approve_and_execute(
        ticket.id, reviewed_by="sarah_analyst"
    )
    assert approved.status == TicketStatus.EXECUTED
    assert approved.execution_result["success"] is True


@pytest.mark.asyncio
async def test_payment_repair_agent_missing_payment():
    """Verify agent safely handles non-existent payment."""
    agent = PaymentRepairAgent()
    result = await agent.run(payment_id="non_existent_id")
    assert result.is_repairable is False
    assert result.status == "NOT_FOUND"
