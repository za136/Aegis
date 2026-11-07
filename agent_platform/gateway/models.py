"""Autonomy Levels, Tool Gateway Contracts, and Approval Inbox Models."""

import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AutonomyLevel(str, enum.Enum):
    """Bounded autonomy ladders per ADR-002 and docs/autonomy-matrix.md."""
    A0_SUGGEST = "A0"          # Agent drafts/recommends; human performs action
    A1_ACT_WITH_APPROVAL = "A1"# Agent prepares action; human must approve in console
    A2_ACT_WITHIN_LIMITS = "A2"# Agent executes autonomously within financial/policy limits
    A3_FULLY_AUTONOMOUS = "A3" # Fully autonomous execution (never for money movement)


class TicketStatus(str, enum.Enum):
    """Lifecycle status of human-in-the-loop approval tickets."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    EXPIRED = "EXPIRED"


class ToolDefinition(BaseModel):
    """Schema metadata for a registered MCP tool."""
    name: str
    description: str
    autonomy_level: AutonomyLevel
    required_squad_roles: List[str] = Field(default_factory=list)
    parameters_schema: Dict[str, Any]
    is_write: bool = False
    max_autonomous_amount: Optional[Decimal] = None


class ToolInvocationRequest(BaseModel):
    """Payload sent by an agent squad to execute a tool via the Gateway."""
    model_config = ConfigDict(frozen=True)

    agent_id: str
    squad_name: str
    tool_name: str
    arguments: Dict[str, Any]
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reasoning: Optional[str] = None


class ToolInvocationResult(BaseModel):
    """Result returned by the Gateway to the agent."""
    correlation_id: str
    tool_name: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    autonomy_level_applied: AutonomyLevel
    approval_required: bool = False
    approval_ticket_id: Optional[str] = None
    execution_time_ms: float = 0.0


class ApprovalTicket(BaseModel):
    """Human-in-the-loop maker-checker review ticket for A1 actions."""
    id: str = Field(default_factory=lambda: f"ticket_{uuid.uuid4().hex[:12]}")
    squad_name: str
    agent_id: str
    tool_name: str
    arguments: Dict[str, Any]
    reasoning: str
    evidence_ids: List[str] = Field(default_factory=list)
    confidence: Optional[float] = None
    amount: Optional[Decimal] = None
    status: TicketStatus = TicketStatus.PENDING
    created_at: datetime = Field(default_factory=utc_now)
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    execution_result: Optional[Any] = None
