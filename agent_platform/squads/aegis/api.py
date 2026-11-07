"""FastAPI REST routes for Aegis Financial Crime Investigation Squad."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from agent_platform.squads.aegis.agent import AegisInvestigationAgent
from agent_platform.squads.aegis.guardrails import scan_for_prompt_injection
from agent_platform.squads.aegis.models import (
    InvestigationCase,
    PolicyExcerpt,
)
from agent_platform.squads.aegis.policy_rag import retrieve_policies
from agent_platform.squads.aegis.tools import MOCK_CASE_STORE

router = APIRouter(prefix="/aegis", tags=["Financial Crime Investigation (Aegis)"])
agent = AegisInvestigationAgent()


class GuardrailCheckRequest(BaseModel):
    text: str


class GuardrailCheckResponse(BaseModel):
    is_hostile: bool
    detected_patterns: List[str]
    status: str


@router.post(
    "/investigate/{alert_id}",
    response_model=InvestigationCase,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger end-to-end financial crime investigation on an alert",
)
async def investigate_alert(alert_id: str) -> InvestigationCase:
    try:
        case = await agent.investigate_alert(alert_id)
        return case
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/cases/{case_id}",
    summary="Get financial crime case dossier and SAR narrative",
)
async def get_case(case_id: str) -> Dict[str, Any]:
    case_data = MOCK_CASE_STORE.get(case_id)
    if not case_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found in case store",
        )
    return case_data


@router.get(
    "/policies",
    response_model=List[PolicyExcerpt],
    summary="Search AML regulatory policies and guidance via Policy RAG",
)
async def search_policies(
    query: str = Query(..., description="AML search query"),
    top_k: int = Query(3, ge=1, le=10),
) -> List[PolicyExcerpt]:
    return retrieve_policies(query, top_k=top_k)


@router.post(
    "/scan-guardrails",
    response_model=GuardrailCheckResponse,
    summary="Scan transaction memo or message for adversarial prompt injection",
)
async def check_guardrails(request: GuardrailCheckRequest) -> GuardrailCheckResponse:
    is_hostile, patterns = scan_for_prompt_injection(request.text)
    return GuardrailCheckResponse(
        is_hostile=is_hostile,
        detected_patterns=patterns,
        status="ALERT_INJECTION_DETECTED" if is_hostile else "CLEAN",
    )
