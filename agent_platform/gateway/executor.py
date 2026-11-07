"""Tool Gateway Executor enforcing autonomy levels, squad permissions, and audit logs."""

import inspect
import time
from decimal import Decimal
from typing import Any, Dict, List, Optional

from agent_platform.gateway.approvals import approval_inbox
from agent_platform.gateway.killswitch import kill_switch
from agent_platform.gateway.models import (
    AutonomyLevel,
    ToolInvocationRequest,
    ToolInvocationResult,
)
from agent_platform.gateway.registry import registry
from services.common.config import settings


class ToolGatewayPermissionError(Exception):
    """Raised when an agent squad lacks permissions to invoke a tool."""
    pass


class ToolGatewayExecutor:
    """Executes tool requests while enforcing bounded autonomy and audit logging."""

    def __init__(self):
        self.inbox = approval_inbox
        self.registry = registry
        # Connect approval execution callback
        self.inbox.set_execution_callback(self._execute_tool_raw)

    async def _execute_tool_raw(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Raw internal execution of a tool handler without autonomy check (e.g. after approval)."""
        handler = self.registry.get_handler(tool_name)
        if not handler:
            raise ValueError(f"Tool handler {tool_name} not found in registry.")

        res = handler(**arguments)
        if inspect.iscoroutine(res):
            res = await res
        return res

    async def invoke_tool(
        self, request: ToolInvocationRequest, squad_roles: Optional[List[str]] = None
    ) -> ToolInvocationResult:
        """Main entrypoint for agent tool invocation enforcing autonomy boundaries."""
        start_time = time.time()
        tool_defn = self.registry.get_tool(request.tool_name)

        if not tool_defn:
            return ToolInvocationResult(
                correlation_id=request.correlation_id,
                tool_name=request.tool_name,
                success=False,
                error=f"Tool '{request.tool_name}' is not registered in Tool Gateway.",
                autonomy_level_applied=AutonomyLevel.A0_SUGGEST,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        # 0. Check Admin Kill Switches (Global Emergency Stop and Per-Squad Switch)
        if kill_switch.state.global_emergency_stop:
            return ToolInvocationResult(
                correlation_id=request.correlation_id,
                tool_name=request.tool_name,
                success=False,
                error=f"Global emergency kill switch engaged: {kill_switch.state.emergency_stop_reason or 'Halted by risk administration'}.",
                autonomy_level_applied=AutonomyLevel.A0_SUGGEST,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        if not kill_switch.is_squad_enabled(request.squad_name):
            return ToolInvocationResult(
                correlation_id=request.correlation_id,
                tool_name=request.tool_name,
                success=False,
                error=f"Squad '{request.squad_name}' has been paused by administrator kill switch.",
                autonomy_level_applied=AutonomyLevel.A0_SUGGEST,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        # 1. Check squad permissions
        if tool_defn.required_squad_roles and squad_roles:
            if not any(role in squad_roles for role in tool_defn.required_squad_roles):
                return ToolInvocationResult(
                    correlation_id=request.correlation_id,
                    tool_name=request.tool_name,
                    success=False,
                    error=f"Squad '{request.squad_name}' lacks required role for {request.tool_name}.",
                    autonomy_level_applied=tool_defn.autonomy_level,
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

        # 2. Autonomy level enforcement with dynamic ceiling clamping
        autonomy = kill_switch.get_effective_autonomy(request.squad_name, tool_defn.autonomy_level)

        # Check if A2 action exceeds financial limits -> escalate to A1
        if autonomy == AutonomyLevel.A2_ACT_WITHIN_LIMITS:
            amount = request.arguments.get("amount")
            if amount is not None:
                amt_dec = Decimal(str(amount))
                default_limit = tool_defn.max_autonomous_amount or Decimal(
                    str(settings.MAX_AUTONOMOUS_TRANSFER_LIMIT_USD)
                )
                limit = kill_switch.get_limit("max_autonomous_transfer_usd", default_limit)
                if amt_dec > limit:
                    # Escalate to A1: requires human approval
                    autonomy = AutonomyLevel.A1_ACT_WITH_APPROVAL

        # If A0: Suggestion only, do not execute
        if autonomy == AutonomyLevel.A0_SUGGEST:
            return ToolInvocationResult(
                correlation_id=request.correlation_id,
                tool_name=request.tool_name,
                success=True,
                data={"status": "DRAFT_SUGGESTION", "arguments": request.arguments},
                autonomy_level_applied=autonomy,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        # If A1: Generate human approval ticket in inbox, DO NOT execute write action
        if autonomy == AutonomyLevel.A1_ACT_WITH_APPROVAL:
            ticket = await self.inbox.create_ticket(
                squad_name=request.squad_name,
                agent_id=request.agent_id,
                tool_name=request.tool_name,
                arguments=request.arguments,
                reasoning=request.reasoning or "Agent proposed write action requiring human authorization.",
            )
            return ToolInvocationResult(
                correlation_id=request.correlation_id,
                tool_name=request.tool_name,
                success=True,
                data={
                    "status": "PENDING_APPROVAL",
                    "ticket_id": ticket.id,
                    "message": "Action routed to human operator in Ops Console for review.",
                },
                autonomy_level_applied=autonomy,
                approval_required=True,
                approval_ticket_id=ticket.id,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        # If A2 or A3: Execute directly
        try:
            data = await self._execute_tool_raw(request.tool_name, request.arguments)
            return ToolInvocationResult(
                correlation_id=request.correlation_id,
                tool_name=request.tool_name,
                success=True,
                data=data,
                autonomy_level_applied=autonomy,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            return ToolInvocationResult(
                correlation_id=request.correlation_id,
                tool_name=request.tool_name,
                success=False,
                error=str(e),
                autonomy_level_applied=autonomy,
                execution_time_ms=(time.time() - start_time) * 1000,
            )


# Global executor singleton
gateway_executor = ToolGatewayExecutor()
