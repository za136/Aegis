"""Unit and Integration Tests for Phase 8 Hardening, Kill Switches, and Dynamic Autonomy Controls."""

from decimal import Decimal
import pytest

from agent_platform.gateway.executor import gateway_executor
from agent_platform.gateway.killswitch import kill_switch
from agent_platform.gateway.models import (
    AutonomyLevel,
    ToolInvocationRequest,
)


@pytest.mark.asyncio
async def test_global_kill_switch_engagement():
    """Verify that engaging the global emergency stop intercepts and rejects all tool calls."""
    try:
        # 1. Engage emergency stop
        kill_switch.engage_global_kill_switch(
            reason="Simulated emergency regulatory freeze",
            operator_id="op_tester_01",
        )
        assert kill_switch.state.global_emergency_stop is True

        # 2. Attempt tool call
        req = ToolInvocationRequest(
            agent_id="test_agent",
            squad_name="payment_repair",
            tool_name="get_payment_details",
            arguments={"payment_id": "pmt_001"},
        )
        result = await gateway_executor.invoke_tool(req, squad_roles=["payment_repair"])

        assert result.success is False
        assert "Global emergency kill switch engaged" in result.error
        assert result.autonomy_level_applied == AutonomyLevel.A0_SUGGEST

    finally:
        # Reset kill switch
        kill_switch.disengage_global_kill_switch(operator_id="op_tester_01")
        assert kill_switch.state.global_emergency_stop is False


@pytest.mark.asyncio
async def test_per_squad_kill_switch_pause():
    """Verify that disabling an individual squad blocks its tools while leaving other squads active."""
    try:
        # 1. Disable onboarding squad
        kill_switch.set_squad_state("onboarding", enabled=False, operator_id="op_tester_01")
        assert kill_switch.is_squad_enabled("onboarding") is False
        assert kill_switch.is_squad_enabled("payment_repair") is True

        # 2. Attempt tool call from disabled squad
        onboarding_req = ToolInvocationRequest(
            agent_id="test_onboarding_agent",
            squad_name="onboarding",
            tool_name="screen_entity_watchlists",
            arguments={"entity_name": "Test Subject"},
        )
        res_blocked = await gateway_executor.invoke_tool(onboarding_req, squad_roles=["onboarding"])
        assert res_blocked.success is False
        assert "Squad 'onboarding' has been paused by administrator kill switch" in res_blocked.error

        # 3. Attempt tool call from active squad -> should proceed
        repair_req = ToolInvocationRequest(
            agent_id="test_repair_agent",
            squad_name="payment_repair",
            tool_name="get_payment_details",
            arguments={"payment_id": "pmt_001"},
        )
        res_active = await gateway_executor.invoke_tool(repair_req, squad_roles=["payment_repair"])
        assert res_active.success is True

    finally:
        # Re-enable onboarding squad
        kill_switch.set_squad_state("onboarding", enabled=True, operator_id="op_tester_01")
        assert kill_switch.is_squad_enabled("onboarding") is True


@pytest.mark.asyncio
async def test_dynamic_autonomy_ceiling_clamping():
    """Verify that clamping a squad's autonomy ceiling forces higher-tier tools to downgrade."""
    try:
        # 1. Normal state: payment repair ceiling is A2
        assert kill_switch.get_effective_autonomy("payment_repair", AutonomyLevel.A2_ACT_WITHIN_LIMITS) == AutonomyLevel.A2_ACT_WITHIN_LIMITS

        # 2. Admin lowers ceiling to A1 (Act with Human Approval only)
        kill_switch.set_squad_autonomy_ceiling("payment_repair", AutonomyLevel.A1_ACT_WITH_APPROVAL, operator_id="op_tester_01")
        effective = kill_switch.get_effective_autonomy("payment_repair", AutonomyLevel.A2_ACT_WITHIN_LIMITS)
        assert effective == AutonomyLevel.A1_ACT_WITH_APPROVAL

        # 3. Admin lowers ceiling to A0 (Suggest Only)
        kill_switch.set_squad_autonomy_ceiling("payment_repair", AutonomyLevel.A0_SUGGEST, operator_id="op_tester_01")
        effective_a0 = kill_switch.get_effective_autonomy("payment_repair", AutonomyLevel.A2_ACT_WITHIN_LIMITS)
        assert effective_a0 == AutonomyLevel.A0_SUGGEST

    finally:
        # Restore ceiling
        kill_switch.set_squad_autonomy_ceiling("payment_repair", AutonomyLevel.A2_ACT_WITHIN_LIMITS, operator_id="op_tester_01")


def test_dynamic_financial_limits_and_audit_trail():
    """Verify financial limits can be updated and are properly logged in the audit trail."""
    initial_count = len(kill_switch.audit_log)

    kill_switch.set_financial_limit(
        limit_key="max_autonomous_transfer_usd",
        amount_usd=Decimal("50.00"),
        operator_id="op_cfo",
    )

    limit = kill_switch.get_limit("max_autonomous_transfer_usd", Decimal("100.00"))
    assert limit == Decimal("50.00")

    # Verify audit log recorded entry
    assert len(kill_switch.audit_log) == initial_count + 1
    last_entry = kill_switch.audit_log[-1]
    assert last_entry.action == "SET_FINANCIAL_LIMIT"
    assert last_entry.target == "max_autonomous_transfer_usd"
    assert last_entry.operator_id == "op_cfo"
    assert "$50.00" in last_entry.details

    # Overview dictionary check
    overview = kill_switch.get_status_overview()
    assert overview["financial_limits"]["max_autonomous_transfer_usd"] == "50.00"
    assert overview["global_emergency_stop"] is False
