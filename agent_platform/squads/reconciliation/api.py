"""FastAPI REST API Endpoints for B2B Invoice Reconciliation."""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from agent_platform.squads.reconciliation.agent import (
    B2BReconciliationAgent,
    ReconciliationAgentReport,
    reconciliation_agent,
)
from agent_platform.squads.reconciliation.tools import BATCH_STORE, DEMO_INVOICES, DEMO_POSTINGS

router = APIRouter(prefix="/reconciliation", tags=["B2B Reconciliation Squad"])


class ReconciliationRunRequest(BaseModel):
    auto_submit_approval: bool = True


@router.post("/run", response_model=ReconciliationAgentReport, summary="Trigger automated B2B reconciliation run")
async def run_reconciliation(req: ReconciliationRunRequest = ReconciliationRunRequest()) -> ReconciliationAgentReport:
    """Execute the multi-pass reconciliation agent to match invoices against ledger postings."""
    return await reconciliation_agent.run(auto_submit_approval=req.auto_submit_approval)


@router.get("/batches/{batch_id}", summary="Get reconciliation batch details")
async def get_reconciliation_batch(batch_id: str) -> Dict[str, Any]:
    """Retrieve details and matches for a specific reconciliation batch."""
    batch = BATCH_STORE.get(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reconciliation batch '{batch_id}' not found.",
        )
    return batch.model_dump(mode="json")


@router.get("/unreconciled-postings", summary="List all unreconciled ledger credits")
async def get_unreconciled_postings() -> List[Dict[str, Any]]:
    """List open credit postings awaiting matching."""
    return [p.model_dump(mode="json") for p in DEMO_POSTINGS.values() if not p.reconciled]


@router.get("/pending-invoices", summary="List pending accounts receivable invoices")
async def get_pending_invoices() -> List[Dict[str, Any]]:
    """List outstanding B2B invoices awaiting payment settlement."""
    return [inv.model_dump(mode="json") for inv in DEMO_INVOICES.values() if inv.status != "PAID"]
