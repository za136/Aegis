"""FastAPI REST routes for Human-in-the-Loop Approvals Inbox."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from agent_platform.gateway.approvals import approval_inbox
from agent_platform.gateway.models import ApprovalTicket, TicketStatus

router = APIRouter(prefix="/approvals", tags=["Approvals Inbox (HITL)"])


class ApprovalActionRequest(BaseModel):
    reviewed_by: str = "analyst"
    reason: Optional[str] = None


@router.get("", response_model=List[ApprovalTicket], summary="List approval tickets")
async def list_tickets(
    status_filter: Optional[TicketStatus] = Query(None, alias="status")
) -> List[ApprovalTicket]:
    return await approval_inbox.list_tickets(status=status_filter)


@router.get("/{ticket_id}", response_model=ApprovalTicket, summary="Get approval ticket details")
async def get_ticket(ticket_id: str) -> ApprovalTicket:
    ticket = await approval_inbox.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval ticket {ticket_id} not found",
        )
    return ticket


@router.post("/{ticket_id}/approve", response_model=ApprovalTicket, summary="Approve and execute A1 action")
async def approve_ticket(
    ticket_id: str, request: ApprovalActionRequest = ApprovalActionRequest()
) -> ApprovalTicket:
    try:
        return await approval_inbox.approve_and_execute(
            ticket_id, reviewed_by=request.reviewed_by
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{ticket_id}/reject", response_model=ApprovalTicket, summary="Reject A1 proposal")
async def reject_ticket(
    ticket_id: str, request: ApprovalActionRequest
) -> ApprovalTicket:
    if not request.reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A rejection reason must be provided",
        )
    try:
        return await approval_inbox.reject_ticket(
            ticket_id, rejection_reason=request.reason, reviewed_by=request.reviewed_by
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
