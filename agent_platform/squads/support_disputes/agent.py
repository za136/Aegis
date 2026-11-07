"""Customer Support & Payment Disputes Squad Agent powered by Google Gemini 3.8 Flash."""

from decimal import Decimal
from typing import Any, Dict, Optional
from pydantic import BaseModel

from agent_platform.gateway.executor import gateway_executor
from agent_platform.gateway.models import ToolInvocationRequest
from agent_platform.squads.support_disputes.models import DisputeResolution, DisputeStatus
from services.common.telemetry import metrics, tracer


SYSTEM_INSTRUCTION = """You are the Senior Consumer Protection & Payment Disputes Specialist for Meridian Bank.
Your objective is to investigate electronic fund transfer disputes pursuant to CFPB Regulation E (12 CFR Part 1005).

Core Principles:
1. Adhere strictly to Regulation E timelines:
   - Notice must be received within 60 calendar days of the periodic statement showing the unauthorized debit (§ 1005.11(b)).
   - If investigation cannot conclude within 10 business days, mandatory provisional credit must be granted (§ 1005.11(c)).
2. Commercial / Business accounts are strictly exempt from Regulation E.
3. Financial credits must be executed through the Tool Gateway under A1 human approval.
"""


class DisputeAgentInvestigationReport(BaseModel):
    claim_id: str
    is_reg_e_eligible: bool
    status: str
    provisional_credit_amount: str
    consumer_liability: str
    chargeback_code: Optional[str] = None
    approval_ticket_id: Optional[str] = None
    regulatory_finding: str
    disposition_summary: str


class SupportDisputesAgent:
    """Autonomous agent investigating customer payment disputes and enforcing Reg E compliance."""

    def __init__(self, model_name: str = "gemini-3.8-flash"):
        self.model_name = model_name
        self.squad_name = "support_disputes"
        self.agent_id = "agent_support_disputes_01"
        self.squad_roles = ["support_disputes", "ops_analyst"]

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any], reasoning: str) -> Any:
        req = ToolInvocationRequest(
            agent_id=self.agent_id,
            squad_name=self.squad_name,
            tool_name=tool_name,
            arguments=arguments,
            reasoning=reasoning,
        )
        return await gateway_executor.invoke_tool(req, squad_roles=self.squad_roles)

    async def run(self, claim_id: str) -> DisputeAgentInvestigationReport:
        """Execute dispute investigation and Reg E assessment pipeline."""
        with tracer.start_span("dispute_investigation_run", squad="support_disputes", claim_id=claim_id) as span:
            # Step 1: Retrieve transaction & claim details
            tx_res = await self._call_tool(
                "get_dispute_transaction",
                {"claim_id": claim_id},
                reasoning=f"Retrieving dispute claim details for {claim_id}",
            )

            if not tx_res.success or not tx_res.data or "error" in tx_res.data:
                return DisputeAgentInvestigationReport(
                    claim_id=claim_id,
                    is_reg_e_eligible=False,
                    status="ERROR",
                    provisional_credit_amount="0.00",
                    consumer_liability="0.00",
                    regulatory_finding="Claim not found in active disputes registry.",
                    disposition_summary="Investigation aborted: Invalid claim ID.",
                )

            claim_data = tx_res.data
            dispute_amt = Decimal(str(claim_data.get("dispute_amount", "0.00")))

            # Step 2: Evaluate Reg E rules
            eval_res = await self._call_tool(
                "evaluate_reg_e_compliance",
                {"claim_id": claim_id},
                reasoning=f"Evaluating 12 CFR Part 1005 statutory compliance for claim {claim_id}",
            )

            assessment_data = eval_res.data.get("assessment", {})
            cb_code = eval_res.data.get("chargeback_network_code")

            is_eligible = assessment_data.get("is_reg_e_eligible", False)
            consumer_liability = str(assessment_data.get("consumer_max_liability", "0.00"))
            provisional_mandated = assessment_data.get("provisional_credit_mandated", False)
            reg_reasoning = assessment_data.get("reasoning", "")

            approval_ticket_id = None
            status = "RESOLVED_INELIGIBLE"
            credit_amount = "0.00"

            if is_eligible and provisional_mandated:
                # Calculate provisional credit amount
                credit_amount = str(dispute_amt)
                credit_res = await self._call_tool(
                    "issue_provisional_credit",
                    {
                        "claim_id": claim_id,
                        "credit_amount": credit_amount,
                        "rationale": f"Reg E mandatory provisional credit: Investigation ongoing past initial intake. {reg_reasoning}",
                    },
                    reasoning=f"Issuing mandatory provisional credit of ${credit_amount} under 12 CFR § 1005.11(c)",
                )

                if credit_res.approval_required:
                    approval_ticket_id = credit_res.ticket_id
                    status = "PENDING_SUPERVISOR_APPROVAL"
                else:
                    status = "PROVISIONAL_CREDIT_GRANTED"

                disposition_summary = (
                    f"Claim validated under Regulation E. Provisional credit of ${credit_amount} recommended. "
                    f"Chargeback network code: {cb_code}. Consumer maximum liability: ${consumer_liability}."
                )
            else:
                disposition_summary = (
                    f"Claim ineligible for Regulation E statutory relief: {reg_reasoning}. "
                    f"Commercial account or notice expired outside 60-day window."
                )

            span.attributes["is_reg_e_eligible"] = is_eligible
            span.attributes["status"] = status
            metrics.payments_processed.inc(1, squad="support_disputes")

            return DisputeAgentInvestigationReport(
                claim_id=claim_id,
                is_reg_e_eligible=is_eligible,
                status=status,
                provisional_credit_amount=credit_amount,
                consumer_liability=consumer_liability,
                chargeback_code=cb_code,
                approval_ticket_id=approval_ticket_id,
                regulatory_finding=reg_reasoning,
                disposition_summary=disposition_summary,
            )


disputes_agent = SupportDisputesAgent()
