"""B2B Invoice & Remittance Reconciliation Squad Agent powered by Google Gemini 3.8 Flash."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from agent_platform.gateway.executor import gateway_executor
from agent_platform.gateway.models import ToolInvocationRequest
from agent_platform.squads.reconciliation.models import ReconciliationBatch
from services.common.telemetry import tracer, metrics


SYSTEM_INSTRUCTION = """You are the Senior Enterprise Accounts Receivable and Reconciliation Specialist for Meridian Bank.
Your task is to review incoming remittance advices and ledger credits, match them against outstanding B2B invoices,
and resolve multi-invoice or partial payment discrepancies.

Rules:
1. Always verify currency and amount matching before proposing settlement.
2. 2-to-1 split payments where one payment settles multiple invoices must be explicitly documented.
3. Any write action updating ledger or invoice records requires accounting supervisor authorization (A1).
"""


class ReconciliationAgentReport(BaseModel):
    batch_id: str
    total_matched_volume: str
    match_count: int
    unmatched_postings_count: int
    unmatched_invoices_count: int
    approval_ticket_id: Optional[str] = None
    status: str  # e.g., "SUBMITTED_FOR_APPROVAL", "NO_MATCHES_FOUND", "PROPOSED"
    summary: str


class B2BReconciliationAgent:
    """Autonomous agent orchestrating multi-pass invoice and remittance reconciliation."""

    def __init__(self, model_name: str = "gemini-3.8-flash"):
        self.model_name = model_name
        self.squad_name = "reconciliation"
        self.agent_id = "agent_reconciliation_01"
        self.squad_roles = ["reconciliation", "ops_analyst"]

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any], reasoning: str) -> Any:
        req = ToolInvocationRequest(
            agent_id=self.agent_id,
            squad_name=self.squad_name,
            tool_name=tool_name,
            arguments=arguments,
            reasoning=reasoning,
        )
        return await gateway_executor.invoke_tool(req, squad_roles=self.squad_roles)

    async def run(self, auto_submit_approval: bool = True) -> ReconciliationAgentReport:
        """Run the end-to-end reconciliation pipeline."""
        with tracer.start_span("b2b_reconciliation_run", squad="reconciliation") as span:
            # Step 1: Query unreconciled postings
            postings_res = await self._call_tool(
                "fetch_unreconciled_postings",
                {},
                reasoning="Retrieving unreconciled credit postings from the core ledger",
            )

            # Step 2: Query outstanding invoices
            invoices_res = await self._call_tool(
                "fetch_pending_invoices",
                {},
                reasoning="Retrieving pending accounts receivable invoices",
            )

            # Step 3: Run multi-pass matcher
            match_res = await self._call_tool(
                "propose_reconciliation_batch",
                {},
                reasoning="Executing multi-pass deterministic invoice matcher",
            )

            if not match_res.success or not match_res.data:
                return ReconciliationAgentReport(
                    batch_id="",
                    total_matched_volume="0.00",
                    match_count=0,
                    unmatched_postings_count=0,
                    unmatched_invoices_count=0,
                    status="ERROR",
                    summary="Failed to generate reconciliation batch.",
                )

            batch_data = match_res.data
            batch_id = batch_data.get("batch_id", "")
            matches = batch_data.get("matches", [])
            matched_vol = str(batch_data.get("total_matched_volume", "0.00"))

            approval_ticket_id = None
            status = "PROPOSED"

            # Step 4: If matches exist and auto_submit_approval is requested, trigger apply_reconciliation_batch (A1 write tool)
            if matches and auto_submit_approval:
                apply_res = await self._call_tool(
                    "apply_reconciliation_batch",
                    {"batch_id": batch_id},
                    reasoning=f"Proposing reconciliation batch {batch_id} with {len(matches)} matches totaling ${matched_vol}",
                )
                if apply_res.approval_required:
                    approval_ticket_id = apply_res.ticket_id
                    status = "PENDING_ACCOUNTING_APPROVAL"
                elif apply_res.success:
                    status = "APPLIED"

            summary = (
                f"Reconciled {len(matches)} payment batches totaling ${matched_vol}. "
                f"Unmatched postings: {len(batch_data.get('unmatched_postings', []))}, "
                f"Unmatched invoices: {len(batch_data.get('unmatched_invoices', []))}."
            )

            span.attributes["matches_count"] = len(matches)
            span.attributes["total_matched_volume"] = matched_vol
            metrics.payments_processed.inc(len(matches), squad="reconciliation")

            return ReconciliationAgentReport(
                batch_id=batch_id,
                total_matched_volume=matched_vol,
                match_count=len(matches),
                unmatched_postings_count=len(batch_data.get("unmatched_postings", [])),
                unmatched_invoices_count=len(batch_data.get("unmatched_invoices", [])),
                approval_ticket_id=approval_ticket_id,
                status=status,
                summary=summary,
            )


reconciliation_agent = B2BReconciliationAgent()
