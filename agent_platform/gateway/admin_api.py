"""Admin API Endpoints for Kill Switches, Autonomy Limits, and Risk Controls."""

from decimal import Decimal
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from agent_platform.gateway.killswitch import kill_switch
from agent_platform.gateway.models import AutonomyLevel

router = APIRouter(prefix="/admin/killswitch", tags=["Admin & Kill Switches"])


class GlobalStopRequest(BaseModel):
    enabled: bool
    reason: str = "Emergency risk intervention"
    operator_id: str = "op_compliance_officer"


class SquadToggleRequest(BaseModel):
    squad_name: str
    enabled: bool
    operator_id: str = "op_compliance_officer"


class AutonomyCeilingRequest(BaseModel):
    squad_name: str
    ceiling: AutonomyLevel
    operator_id: str = "op_compliance_officer"


class FinancialLimitRequest(BaseModel):
    limit_key: str
    limit_usd: Decimal = Field(..., gt=0)
    operator_id: str = "op_compliance_officer"


@router.get("", summary="Get global kill switch status and squad autonomy overview")
async def get_killswitch_status() -> Dict[str, Any]:
    """Retrieve live kill switches, squad states, and financial limit ceilings."""
    return kill_switch.get_status_overview()


@router.post("/global", summary="Engage or disengage global emergency stop")
async def set_global_emergency_stop(req: GlobalStopRequest) -> Dict[str, Any]:
    """Toggle the global kill switch halting all agent tool executions."""
    if req.enabled:
        kill_switch.engage_global_kill_switch(reason=req.reason, operator_id=req.operator_id)
    else:
        kill_switch.disengage_global_kill_switch(operator_id=req.operator_id)
    return kill_switch.get_status_overview()


@router.post("/squad", summary="Toggle squad execution state")
async def set_squad_state(req: SquadToggleRequest) -> Dict[str, Any]:
    """Enable or disable a specific agent squad."""
    if req.squad_name not in kill_switch.state.squad_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Squad '{req.squad_name}' not found.",
        )
    kill_switch.set_squad_state(req.squad_name, req.enabled, operator_id=req.operator_id)
    return kill_switch.get_status_overview()


@router.post("/autonomy-ceiling", summary="Clamp maximum autonomy ceiling for a squad")
async def set_autonomy_ceiling(req: AutonomyCeilingRequest) -> Dict[str, Any]:
    """Set the maximum autonomy level an agent squad is allowed to execute."""
    kill_switch.set_squad_autonomy_ceiling(req.squad_name, req.ceiling, operator_id=req.operator_id)
    return kill_switch.get_status_overview()


@router.post("/financial-limit", summary="Update dynamic financial autonomy threshold")
async def set_financial_limit(req: FinancialLimitRequest) -> Dict[str, Any]:
    """Adjust financial limits for autonomous execution (A2)."""
    kill_switch.set_financial_limit(req.limit_key, req.limit_usd, operator_id=req.operator_id)
    return kill_switch.get_status_overview()


@router.get("/audit", summary="Get kill switch change audit history")
async def get_killswitch_audit_log() -> List[Dict[str, Any]]:
    """Retrieve full audit log of all kill switch and autonomy changes."""
    return [entry.model_dump(mode="json") for entry in kill_switch.audit_log]
