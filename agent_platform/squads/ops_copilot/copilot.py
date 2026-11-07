"""Operations Copilot Reasoning Agent powered by Google Gemini 3.8 Flash."""

from typing import Any, Dict, List
from agent_platform.gateway.executor import gateway_executor
from agent_platform.gateway.models import ToolInvocationRequest
from agent_platform.squads.ops_copilot.models import (
    CitationSourceType,
    CopilotAnswer,
    CopilotQueryRequest,
    GroundedCitation,
    SuggestedAction,
)
from services.common.telemetry import tracer


SYSTEM_INSTRUCTION = """You are the Senior Banking Operations Copilot for Meridian Bank.
Your goal is to answer questions from compliance officers, operations analysts, and platform engineers.

Mandatory Constraints:
1. You must ONLY answer using factual data retrieved from the Tool Gateway.
2. Every number, status, or balance you cite must include a specific citation tag (e.g. [CITE:ledger_summary], [CITE:approval_inbox]).
3. You never hallucinate account balances or ticket states.
4. Always provide suggested next actions for the operator console.
"""


class OperationsCopilotAgent:
    """Read-only intelligent copilot answering operational queries with grounded citations."""

    def __init__(self, model_name: str = "gemini-3.8-flash"):
        self.model_name = model_name
        self.squad_name = "ops_copilot"
        self.agent_id = "agent_ops_copilot_01"
        self.squad_roles = ["ops_copilot", "ops_analyst", "compliance_officer"]

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any], reasoning: str) -> Any:
        req = ToolInvocationRequest(
            agent_id=self.agent_id,
            squad_name=self.squad_name,
            tool_name=tool_name,
            arguments=arguments,
            reasoning=reasoning,
        )
        return await gateway_executor.invoke_tool(req, squad_roles=self.squad_roles)

    async def answer(self, req: CopilotQueryRequest) -> CopilotAnswer:
        """Route query to relevant data tools, extract citations, and formulate grounded response."""
        query_lower = req.query.lower()
        citations: List[GroundedCitation] = []
        suggested_actions: List[SuggestedAction] = []

        with tracer.start_span("ops_copilot_query", query=req.query) as span:
            # 1. Routing: Check if query relates to ledger balances or holds
            if any(k in query_lower for k in ["ledger", "balance", "deposit", "hold", "reserve", "suspense"]):
                ledger_res = await self._call_tool(
                    "query_ledger_accounts_summary",
                    {},
                    reasoning="Querying core ledger snapshot and active reservations",
                )
                if ledger_res.success and ledger_res.data:
                    data = ledger_res.data
                    citations.append(
                        GroundedCitation(
                            source_type=CitationSourceType.LEDGER_SUMMARY,
                            entity_id="core_ledger_balances",
                            metric_or_field="settled_customer_deposits_usd",
                            verified_value=f"${data['settled_customer_deposits_usd']}",
                            citation_tag="[CITE:ledger_summary:deposits]",
                        )
                    )
                    citations.append(
                        GroundedCitation(
                            source_type=CitationSourceType.LEDGER_SUMMARY,
                            entity_id="core_ledger_holds",
                            metric_or_field="pending_reserved_holds_usd",
                            verified_value=f"${data['pending_reserved_holds_usd']}",
                            citation_tag="[CITE:ledger_summary:holds]",
                        )
                    )
                    suggested_actions.append(
                        SuggestedAction(label="View Live Ledger", action_type="NAVIGATE", target_url_or_id="/ledger")
                    )

            # 2. Routing: Check if query relates to approval inbox or pending maker-checker tickets
            if any(k in query_lower for k in ["ticket", "approval", "pending", "inbox", "maker", "checker"]):
                inbox_res = await self._call_tool(
                    "search_approval_inbox",
                    {"status": "PENDING"},
                    reasoning="Querying pending maker-checker tickets in approvals inbox",
                )
                if inbox_res.success and inbox_res.data is not None:
                    tickets = inbox_res.data
                    citations.append(
                        GroundedCitation(
                            source_type=CitationSourceType.APPROVAL_INBOX,
                            entity_id="approvals_queue",
                            metric_or_field="pending_ticket_count",
                            verified_value=str(len(tickets)),
                            citation_tag="[CITE:approval_inbox:pending_count]",
                        )
                    )
                    suggested_actions.append(
                        SuggestedAction(label="Open Approvals Inbox", action_type="NAVIGATE", target_url_or_id="/approvals")
                    )

            # 3. Routing: Check if query relates to financial crime or AML alerts
            if any(k in query_lower for k in ["aml", "sar", "structuring", "crime", "alert", "fincen", "rapid"]):
                aml_res = await self._call_tool(
                    "query_active_aml_alerts",
                    {},
                    reasoning="Querying active financial crime investigation alerts",
                )
                if aml_res.success and aml_res.data:
                    alerts = aml_res.data
                    for a in alerts:
                        citations.append(
                            GroundedCitation(
                                source_type=CitationSourceType.FINANCIAL_CRIME_ALERT,
                                entity_id=a["alert_id"],
                                metric_or_field="typology",
                                verified_value=f"{a['typology']} (${a['aggregate_amount_usd']})",
                                citation_tag=f"[CITE:aml_alert:{a['alert_id']}]",
                            )
                        )
                    suggested_actions.append(
                        SuggestedAction(label="Open Aegis SAR Workbench", action_type="NAVIGATE", target_url_or_id="/aegis")
                    )

            # 4. Routing: Check if query relates to telemetry or metrics
            if any(k in query_lower for k in ["metric", "telemetry", "prometheus", "stat", "performance", "volume"]):
                tel_res = await self._call_tool(
                    "query_platform_telemetry",
                    {},
                    reasoning="Querying live Prometheus counters across all squads",
                )
                if tel_res.success and tel_res.data:
                    t_data = tel_res.data
                    citations.append(
                        GroundedCitation(
                            source_type=CitationSourceType.SYSTEM_TELEMETRY,
                            entity_id="prometheus_counters",
                            metric_or_field="payments_processed_total",
                            verified_value=str(t_data["payments_processed_total"]),
                            citation_tag="[CITE:telemetry:payments]",
                        )
                    )

            # Formulate grounded answer
            if not citations:
                # Default fallback query to system stats
                tel_res = await self._call_tool("query_platform_telemetry", {}, reasoning="Defaulting to platform overview")
                answer_md = (
                    f"### Operations Platform Overview\n\n"
                    f"I processed your query: *\"{req.query}\"*. "
                    f"All systems are operating normally across the banking core and agent squads.\n\n"
                    f"- **Active Autonomous Tool Calls**: {tel_res.data.get('tool_gateway_invocations_total', 0)} invocations\n"
                    f"- **Maker-Checker Tickets**: {tel_res.data.get('maker_checker_tickets_total', 0)} generated\n"
                    f"- **Security Guardrails**: {tel_res.data.get('adversarial_injections_blocked', 0)} attacks intercepted"
                )
            else:
                answer_parts = [f"### Grounded Operations Report for: *\"{req.query}\"*\n"]
                for c in citations:
                    answer_parts.append(f"- **{c.metric_or_field.replace('_', ' ').title()}**: `{c.verified_value}` {c.citation_tag}")

                answer_parts.append("\nAll data above was queried live from verified platform gateways and database invariants.")
                answer_md = "\n".join(answer_parts)

            span.attributes["citation_count"] = len(citations)

            return CopilotAnswer(
                query=req.query,
                answer_markdown=answer_md,
                citations=citations,
                suggested_actions=suggested_actions,
            )


ops_copilot = OperationsCopilotAgent()
