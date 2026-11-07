"""Unit and Contract Tests for MCP Tool Gateway, Autonomy Enforcement, and Approvals."""

import pytest
from agent_platform.gateway.approvals import approval_inbox
from agent_platform.gateway.executor import gateway_executor
from agent_platform.gateway.models import (
    AutonomyLevel,
    TicketStatus,
    ToolInvocationRequest,
)
from agent_platform.gateway.registry import registry
import agent_platform.gateway.tools  # Ensure tools are registered


@pytest.mark.asyncio
async def test_tool_registry_and_gemini_export():
    """Verify tool definitions and Gemini function declaration exports."""
    tools = registry.list_tools()
    tool_names = [t.name for t in tools]
    assert "get_payment_details" in tool_names
    assert "lookup_counterparty_directory" in tool_names
    assert "propose_payment_repair" in tool_names

    # Check Gemini schema conversion
    gemini_tools = registry.to_gemini_tools(squad_roles=["payment_repair"])
    repair_tool = next(t for t in gemini_tools if t["name"] == "propose_payment_repair")
    assert "parameters" in repair_tool
    assert "corrected_account_number" in repair_tool["parameters"]["properties"]


@pytest.mark.asyncio
async def test_gateway_read_tool_execution():
    """Verify read-only tools execute directly within A2 limits."""
    req = ToolInvocationRequest(
        agent_id="test_agent",
        squad_name="payment_repair",
        tool_name="get_payment_details",
        arguments={"payment_id": "pmt_ex_101"},
    )
    result = await gateway_executor.invoke_tool(req, squad_roles=["payment_repair"])
    assert result.success is True
    assert result.approval_required is False
    assert result.data["id"] == "pmt_ex_101"
    assert result.data["rejection_code"] == "AC04"


@pytest.mark.asyncio
async def test_gateway_permission_enforcement():
    """Verify squad lacking required roles is rejected by Gateway."""
    req = ToolInvocationRequest(
        agent_id="rogue_agent",
        squad_name="unauthorized_squad",
        tool_name="propose_payment_repair",
        arguments={
            "payment_id": "pmt_ex_101",
            "corrected_account_number": "US99BOFA1122334",
            "repair_reason": "Testing unauthorized",
        },
    )
    # Give it unrelated role
    result = await gateway_executor.invoke_tool(req, squad_roles=["guest_viewer"])
    assert result.success is False
    assert "lacks required role" in result.error


@pytest.mark.asyncio
async def test_gateway_a1_autonomy_approval_ticket():
    """Verify A1 write actions do NOT execute directly and create pending approval tickets."""
    req = ToolInvocationRequest(
        agent_id="repair_agent",
        squad_name="payment_repair",
        tool_name="propose_payment_repair",
        arguments={
            "payment_id": "pmt_ex_101",
            "corrected_account_number": "US33WELL9988222",
            "repair_reason": "Verified active account in directory",
        },
        reasoning="Account closed at counterparty; replacement active account identified",
    )
    result = await gateway_executor.invoke_tool(req, squad_roles=["payment_repair"])
    assert result.success is True
    assert result.approval_required is True
    assert result.approval_ticket_id is not None
    assert result.data["status"] == "PENDING_APPROVAL"

    # Verify ticket exists in approval inbox
    ticket = await approval_inbox.get_ticket(result.approval_ticket_id)
    assert ticket is not None
    assert ticket.status == TicketStatus.PENDING
    assert ticket.arguments["corrected_account_number"] == "US33WELL9988222"

    # Human analyst approves the ticket
    approved_ticket = await approval_inbox.approve_and_execute(
        ticket.id, reviewed_by="sarah_analyst"
    )
    assert approved_ticket.status == TicketStatus.EXECUTED
    assert approved_ticket.reviewed_by == "sarah_analyst"
    assert approved_ticket.execution_result["success"] is True


@pytest.mark.asyncio
async def test_gateway_ticket_rejection():
    """Verify human analyst can reject an A1 proposal with a reason."""
    ticket = await approval_inbox.create_ticket(
        squad_name="payment_repair",
        agent_id="test_agent",
        tool_name="propose_payment_repair",
        arguments={"payment_id": "pmt_999"},
        reasoning="Test rejection",
    )
    assert ticket.status == TicketStatus.PENDING

    rejected_ticket = await approval_inbox.reject_ticket(
        ticket.id, rejection_reason="Account checksum mismatch", reviewed_by="sarah_analyst"
    )
    assert rejected_ticket.status == TicketStatus.REJECTED
    assert rejected_ticket.rejection_reason == "Account checksum mismatch"
