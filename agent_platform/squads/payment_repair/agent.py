"""Payment Exception Repair Agent Squad powered by Google Gemini 3.8 Flash & Tool Gateway."""

import json
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from agent_platform.gateway.executor import gateway_executor
from agent_platform.gateway.models import ToolInvocationRequest
from agent_platform.gateway.registry import registry
from agent_platform.squads.payment_repair.diagnostics import diagnose_rejection_code
from services.common.config import settings

SYSTEM_INSTRUCTION = """You are the Lead Payment Operations Repair Specialist for Meridian Bank.
Your objective is to diagnose rejected payment instructions (ISO 20022 exceptions such as AC04, AC01, BE05),
inspect the underlying reason, consult verified counterparty directories, and formulate a safe repair proposal.

Core Operating Constraints:
1. You NEVER directly mutate ledger balances or bypass banking controls.
2. All repair actions must be proposed via the 'propose_payment_repair' tool, which requires human-in-the-loop (A1) sign-off.
3. Always cite specific evidence (directory matches, reason codes) in your repair rationale.
4. If an exception cannot be repaired safely (e.g. AM04 Insufficient Funds), explain clearly why and recommend returning the payment.
"""


class PaymentRepairResult(BaseModel):
    """Structured disposition of a payment repair investigation."""
    payment_id: str
    rejection_code: Optional[str] = None
    diagnosed_cause: str
    is_repairable: bool
    proposed_account_number: Optional[str] = None
    confidence: float
    rationale: str
    approval_ticket_id: Optional[str] = None
    status: str  # e.g., PENDING_APPROVAL, UNREPAIRABLE, COMPLETED


class PaymentRepairAgent:
    """Autonomous agent investigating and repairing stuck or rejected payments."""

    def __init__(self, model_name: str = "gemini-3.8-flash"):
        self.model_name = model_name
        self.squad_name = "payment_repair"
        self.agent_id = "agent_payment_repair_01"
        self.squad_roles = ["payment_repair", "ops_analyst"]
        self.max_steps = 5

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any], reasoning: str) -> Any:
        """Invoke a tool exclusively via the Gateway."""
        req = ToolInvocationRequest(
            agent_id=self.agent_id,
            squad_name=self.squad_name,
            tool_name=tool_name,
            arguments=arguments,
            reasoning=reasoning,
        )
        res = await gateway_executor.invoke_tool(req, squad_roles=self.squad_roles)
        return res

    async def run(self, payment_id: str) -> PaymentRepairResult:
        """Run the diagnosis and repair investigation loop for a payment."""
        # Step 1: Tool Gateway call to get payment details
        details_res = await self._call_tool(
            "get_payment_details",
            {"payment_id": payment_id},
            reasoning="Inspecting payment failure details and state history",
        )

        if not details_res.success or not details_res.data or "error" in details_res.data:
            return PaymentRepairResult(
                payment_id=payment_id,
                diagnosed_cause="Payment record not found on ledger",
                is_repairable=False,
                confidence=0.0,
                rationale="Unable to locate payment in the core system.",
                status="NOT_FOUND",
            )

        pmt = details_res.data
        rejection_code = pmt.get("rejection_code") or "UNKNOWN"
        creditor_name = pmt.get("creditor_name", "")

        # Step 2: Diagnostic rule consultation
        rule = diagnose_rejection_code(rejection_code)
        if rule and not rule.repairable:
            return PaymentRepairResult(
                payment_id=payment_id,
                rejection_code=rejection_code,
                diagnosed_cause=rule.meaning,
                is_repairable=False,
                confidence=1.0,
                rationale=f"Code {rejection_code} indicates an unrepairable condition: {rule.meaning}. Action: Release hold.",
                status="UNREPAIRABLE",
            )

        # Step 3: Tool Gateway call to lookup counterparty directory for verified account
        cp_res = await self._call_tool(
            "lookup_counterparty_directory",
            {"name": creditor_name},
            reasoning=f"Looking up verified routing profile for counterparty {creditor_name}",
        )

        if not cp_res.success or not cp_res.data or not cp_res.data.get("found"):
            return PaymentRepairResult(
                payment_id=payment_id,
                rejection_code=rejection_code,
                diagnosed_cause=f"Rejection {rejection_code}; counterparty directory lookup yielded no active profile",
                is_repairable=False,
                confidence=0.6,
                rationale=f"No verified replacement routing details found for {creditor_name}.",
                status="MANUAL_INVESTIGATION_REQUIRED",
            )

        verified_acct = cp_res.data["verified_account_number"]

        # Step 4: Propose repair via Tool Gateway (A1 Autonomy requires Human Approval)
        repair_rationale = (
            f"Payment was rejected with code {rejection_code} ({rule.meaning if rule else 'Failure'}). "
            f"Counterparty directory confirms active verified account {verified_acct} for {creditor_name}."
        )

        repair_res = await self._call_tool(
            "propose_payment_repair",
            {
                "payment_id": payment_id,
                "corrected_account_number": verified_acct,
                "repair_reason": repair_rationale,
            },
            reasoning=repair_rationale,
        )

        return PaymentRepairResult(
            payment_id=payment_id,
            rejection_code=rejection_code,
            diagnosed_cause=rule.meaning if rule else "Counterparty account error",
            is_repairable=True,
            proposed_account_number=verified_acct,
            confidence=0.98,
            rationale=repair_rationale,
            approval_ticket_id=repair_res.approval_ticket_id,
            status="PENDING_APPROVAL" if repair_res.approval_required else "REPAIRED",
        )
