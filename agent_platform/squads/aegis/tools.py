"""Registered Tool Gateway tools for the Aegis Financial Crime Investigation Squad."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from agent_platform.gateway.models import AutonomyLevel
from agent_platform.gateway.registry import register_tool
from agent_platform.squads.aegis.analyzer import analyzer
from agent_platform.squads.aegis.policy_rag import retrieve_policies
from agent_platform.squads.onboarding.watchlists import screen_name

# Mock Store for Alerts, Cases, and SAR Filings
MOCK_ALERT_STORE: Dict[str, Dict[str, Any]] = {
    "alt_struct_001": {
        "alert_id": "alt_struct_001",
        "account_id": "acc_cust_struct_01",
        "customer_id": "cust_john_doe",
        "account_number": "US12MERI0009988",
        "typology_hint": "STRUCTURING",
        "severity": "HIGH",
        "created_at": "2026-11-06T14:00:00Z",
        "transactions": [
            {"id": "tx_smurf_01", "amount": "9500.00", "type": "CREDIT", "direction": "INCOMING", "date": "2026-11-05T09:30:00Z", "memo": "Consulting services phase 1"},
            {"id": "tx_smurf_02", "amount": "9800.00", "type": "CREDIT", "direction": "INCOMING", "date": "2026-11-05T14:15:00Z", "memo": "Equipment delivery advance"},
            {"id": "tx_smurf_03", "amount": "9200.00", "type": "CREDIT", "direction": "INCOMING", "date": "2026-11-06T10:00:00Z", "memo": "Software maintenance retainer"},
            {"id": "tx_wire_out_01", "amount": "28000.00", "type": "DEBIT", "direction": "OUTGOING", "date": "2026-11-06T13:45:00Z", "memo": "Offshore procurement wire"},
        ],
    },
    "alt_rapid_002": {
        "alert_id": "alt_rapid_002",
        "account_id": "acc_mule_02",
        "customer_id": "cust_fast_flow",
        "account_number": "US12MERI0005544",
        "typology_hint": "RAPID_MOVEMENT",
        "severity": "HIGH",
        "created_at": "2026-11-06T16:00:00Z",
        "transactions": [
            {"id": "tx_rapid_in_01", "amount": "45000.00", "type": "CREDIT", "direction": "INCOMING", "date": "2026-11-06T14:00:00Z", "memo": "Investor capital seed"},
            {"id": "tx_rapid_out_01", "amount": "44900.00", "type": "DEBIT", "direction": "OUTGOING", "latency_hours": 1.2, "date": "2026-11-06T15:12:00Z", "memo": "Immediate cashout distribution"},
        ],
    },
}

MOCK_CASE_STORE: Dict[str, Dict[str, Any]] = {}


class AlertDetailsArgs(BaseModel):
    alert_id: str = Field(..., description="ID of the financial crime alert to investigate")


@register_tool(
    name="get_alert_details",
    description="Fetch financial crime alert metadata, customer ID, and triggering transaction batches.",
    autonomy_level=AutonomyLevel.A2_ACT_WITHIN_LIMITS,
    is_write=False,
    required_squad_roles=["financial_crime", "compliance_officer"],
    schema_model=AlertDetailsArgs,
)
def get_alert_details(alert_id: str) -> Dict[str, Any]:
    alert = MOCK_ALERT_STORE.get(alert_id)
    if not alert:
        return {"error": f"Alert {alert_id} not found in alert store."}
    return alert


class AccountAnalysisArgs(BaseModel):
    account_id: str = Field(..., description="Account ID to analyze for AML typologies")
    lookback_days: int = Field(default=30, description="Rolling historical lookback window in days")


@register_tool(
    name="analyze_account_transactions",
    description="Run algorithmic pattern detection for Structuring, Rapid Movement, and Layering over transaction graph.",
    autonomy_level=AutonomyLevel.A2_ACT_WITHIN_LIMITS,
    is_write=False,
    required_squad_roles=["financial_crime", "compliance_officer"],
    schema_model=AccountAnalysisArgs,
)
def analyze_account_transactions(account_id: str, lookback_days: int = 30) -> Dict[str, Any]:
    # Locate transactions for account
    txs = []
    for alert in MOCK_ALERT_STORE.values():
        if alert.get("account_id") == account_id:
            txs = alert.get("transactions", [])
            break

    struct_findings = analyzer.analyze_structuring(txs)
    rapid_findings = analyzer.analyze_rapid_movement(txs)

    all_findings = [f.model_dump() for f in (struct_findings + rapid_findings)]
    return {
        "account_id": account_id,
        "analyzed_transactions_count": len(txs),
        "findings_count": len(all_findings),
        "findings": all_findings,
    }


class PolicyRetrieveArgs(BaseModel):
    query: str = Field(..., description="AML query string, e.g. 'structuring threshold' or 'pass-through'")
    top_k: int = Field(default=3, description="Maximum number of policy excerpts to retrieve")


@register_tool(
    name="retrieve_aml_policies",
    description="Perform semantic search over FATF, FinCEN CTR rules, and bank AML policy manual.",
    autonomy_level=AutonomyLevel.A2_ACT_WITHIN_LIMITS,
    is_write=False,
    required_squad_roles=["financial_crime", "compliance_officer"],
    schema_model=PolicyRetrieveArgs,
)
def retrieve_aml_policies(query: str, top_k: int = 3) -> Dict[str, Any]:
    excerpts = retrieve_policies(query, top_k=top_k)
    return {
        "query": query,
        "count": len(excerpts),
        "excerpts": [e.model_dump() for e in excerpts],
    }


class FileSARDossierArgs(BaseModel):
    case_id: str
    customer_id: str
    narrative_summary: str
    cited_evidence_ids: List[str]
    recommended_disposition: str  # FILE_SAR, CLOSE_NO_ACTION, REQUEST_RFI


@register_tool(
    name="file_sar_dossier",
    description="Submit finalized Suspicious Activity Report (SAR) dossier for mandatory Compliance Officer / MLRO review (A1).",
    autonomy_level=AutonomyLevel.A1_ACT_WITH_APPROVAL,
    is_write=True,
    required_squad_roles=["financial_crime"],
    schema_model=FileSARDossierArgs,
)
def file_sar_dossier(
    case_id: str,
    customer_id: str,
    narrative_summary: str,
    cited_evidence_ids: List[str],
    recommended_disposition: str,
) -> Dict[str, Any]:
    MOCK_CASE_STORE[case_id] = {
        "case_id": case_id,
        "customer_id": customer_id,
        "narrative_summary": narrative_summary,
        "cited_evidence_ids": cited_evidence_ids,
        "recommended_disposition": recommended_disposition,
        "status": "PENDING_APPROVAL",
    }
    return {
        "success": True,
        "case_id": case_id,
        "status": "SUBMITTED_FOR_MLRO_APPROVAL",
        "message": f"Case dossier {case_id} submitted. Awaiting compliance officer authorization.",
    }
