"""FastAPI REST API Endpoints for Customer Support & Payment Disputes Squad."""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from agent_platform.squads.support_disputes.agent import (
    DisputeAgentInvestigationReport,
    SupportDisputesAgent,
    disputes_agent,
)
from agent_platform.squads.support_disputes.models import DisputeClaim
from agent_platform.squads.support_disputes.tools import (
    DEMO_DISPUTE_CLAIMS,
    DISPUTE_RESOLUTIONS,
)

router = APIRouter(prefix="/disputes", tags=["Support & Disputes Squad"])


@router.post("/claims/{claim_id}/investigate", response_model=DisputeAgentInvestigationReport, summary="Trigger automated Reg E dispute investigation")
async def investigate_dispute(claim_id: str) -> DisputeAgentInvestigationReport:
    """Execute the Reg E investigation and provisional credit evaluation pipeline."""
    return await disputes_agent.run(claim_id)


@router.get("/claims/{claim_id}", summary="Get dispute claim details")
async def get_dispute_claim(claim_id: str) -> Dict[str, Any]:
    """Retrieve details for a specific customer dispute claim."""
    claim = DEMO_DISPUTE_CLAIMS.get(claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispute claim '{claim_id}' not found.",
        )
    return claim.model_dump(mode="json")


@router.get("/claims", summary="List all customer dispute claims")
async def list_dispute_claims() -> List[Dict[str, Any]]:
    """List open and investigated customer dispute claims."""
    return [claim.model_dump(mode="json") for claim in DEMO_DISPUTE_CLAIMS.values()]
