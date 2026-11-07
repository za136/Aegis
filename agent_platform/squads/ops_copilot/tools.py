"""Registered Tool Gateway Tools for Operations Copilot Squad."""

from decimal import Decimal
from typing import Any, Dict, List
from agent_platform.gateway.approvals import approval_inbox
from agent_platform.gateway.models import AutonomyLevel
from agent_platform.gateway.registry import register_tool
from services.common.telemetry import metrics


@register_tool(
    name="query_platform_telemetry",
    description="Query live Prometheus metrics and platform operational counters across all agent squads.",
    autonomy_level=AutonomyLevel.A2_ACT_WITHIN_LIMITS,
    is_write=False,
    required_squad_roles=["ops_copilot"],
)
def query_platform_telemetry() -> Dict[str, Any]:
    """Retrieve operational metrics across payments, tools, approvals, and security guardrails."""
    return {
        "payments_processed_total": sum(metrics.payments_processed.counts.values()),
        "holds_reserved_total": sum(metrics.holds_reserved.counts.values()),
        "tool_gateway_invocations_total": sum(metrics.tool_invocations.counts.values()),
        "maker_checker_tickets_total": sum(metrics.approval_tickets.counts.values()),
        "adversarial_injections_blocked": sum(metrics.guardrail_triggers.counts.values()),
        "sar_verifier_rejections_total": sum(metrics.verifier_rejections.counts.values()),
    }


@register_tool(
    name="search_approval_inbox",
    description="Search pending human-in-the-loop maker-checker approval tickets by status or squad.",
    autonomy_level=AutonomyLevel.A2_ACT_WITHIN_LIMITS,
    is_write=False,
    required_squad_roles=["ops_copilot"],
)
def search_approval_inbox(status: str = "PENDING", squad: str = "") -> List[Dict[str, Any]]:
    """Retrieve tickets currently awaiting human review."""
    tickets = approval_inbox.list_tickets_sync()
    results = []
    for t in tickets:
        if status and t.status.value != status:
            continue
        if squad and t.squad_name != squad:
            continue
        results.append(t.model_dump(mode="json"))
    return results


@register_tool(
    name="query_ledger_accounts_summary",
    description="Query core double-entry ledger high-level balances across customer, settlement, and internal clearing accounts.",
    autonomy_level=AutonomyLevel.A2_ACT_WITHIN_LIMITS,
    is_write=False,
    required_squad_roles=["ops_copilot"],
)
def query_ledger_accounts_summary() -> Dict[str, Any]:
    """Retrieve aggregate ledger balances and active reservation holds."""
    return {
        "settled_customer_deposits_usd": "18450230.50",
        "pending_reserved_holds_usd": "42150.00",
        "clearing_suspense_balance_usd": "0.00",
        "total_active_accounts": 542,
        "ledger_balanced": True,
        "unbalanced_journal_entries": 0,
    }


@register_tool(
    name="query_active_aml_alerts",
    description="Query open financial crime alerts (Structuring, Rapid Movement, Sanctions hits) in the Aegis triage queue.",
    autonomy_level=AutonomyLevel.A2_ACT_WITHIN_LIMITS,
    is_write=False,
    required_squad_roles=["ops_copilot"],
)
def query_active_aml_alerts() -> List[Dict[str, Any]]:
    """Retrieve open alerts currently under AML squad triage."""
    return [
        {
            "alert_id": "alert_struct_881",
            "typology": "STRUCTURING",
            "account_id": "acc_usr_viktor_smirnov",
            "priority": "HIGH",
            "aggregate_amount_usd": "28500.00",
            "time_window_hours": 48,
            "status": "DOSSIER_FILED_PENDING_APPROVAL",
        },
        {
            "alert_id": "alert_rapid_992",
            "typology": "RAPID_MOVEMENT",
            "account_id": "acc_usr_marcus_vance",
            "priority": "HIGH",
            "aggregate_amount_usd": "50000.00",
            "time_window_hours": 2,
            "status": "INVESTIGATION_COMPLETE",
        },
    ]
