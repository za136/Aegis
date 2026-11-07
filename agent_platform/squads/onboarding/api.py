"""FastAPI REST routes for Customer Onboarding and KYC Screening."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from agent_platform.squads.onboarding.agent import OnboardingAgent
from agent_platform.squads.onboarding.models import (
    OnboardingApplicationRequest,
    OnboardingDisposition,
    ScreeningMatch,
)
from agent_platform.squads.onboarding.tools import ONBOARDING_STORE
from agent_platform.squads.onboarding.watchlists import screen_name

router = APIRouter(prefix="/onboarding", tags=["Customer Onboarding & KYC"])
agent = OnboardingAgent()


@router.post(
    "/apply",
    response_model=OnboardingDisposition,
    status_code=status.HTTP_201_CREATED,
    summary="Submit customer onboarding application for autonomous KYC evaluation",
)
async def submit_application(
    request: OnboardingApplicationRequest,
) -> OnboardingDisposition:
    disposition = await agent.evaluate_application(request)
    return disposition


@router.get(
    "/applications/{application_id}",
    summary="Get onboarding application disposition and status",
)
async def get_application(application_id: str) -> Dict[str, Any]:
    app_data = ONBOARDING_STORE.get(application_id)
    if not app_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found",
        )
    return app_data


@router.get(
    "/applications",
    summary="List all evaluated applications",
)
async def list_applications() -> List[Dict[str, Any]]:
    return list(ONBOARDING_STORE.values())


@router.get(
    "/screen",
    response_model=List[ScreeningMatch],
    summary="Ad-hoc Sanctions & PEP watchlist screening",
)
async def screen_entity(
    name: str = Query(..., description="Entity or individual name to screen"),
    threshold: float = Query(0.80, ge=0.5, le=1.0),
) -> List[ScreeningMatch]:
    return screen_name(name, threshold=threshold)
