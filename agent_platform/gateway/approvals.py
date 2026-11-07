"""Approval Inbox Service managing Human-in-the-Loop review for A1 agent actions."""

import inspect
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from agent_platform.gateway.models import ApprovalTicket, TicketStatus


class ApprovalInbox:
    """In-memory & DB-backed approval queue for human maker-checker reviews."""

    def __init__(self):
        self._tickets: Dict[str, ApprovalTicket] = {}
        self._execution_callback: Optional[Callable] = None

    def set_execution_callback(self, callback: Callable):
        """Set callback to invoke when an approved ticket is executed."""
        self._execution_callback = callback

    async def create_ticket(
        self,
        squad_name: str,
        agent_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        reasoning: str,
        evidence_ids: Optional[List[str]] = None,
        confidence: Optional[float] = None,
    ) -> ApprovalTicket:
        """Create a new pending approval ticket for an A1 action."""
        ticket = ApprovalTicket(
            squad_name=squad_name,
            agent_id=agent_id,
            tool_name=tool_name,
            arguments=arguments,
            reasoning=reasoning,
            evidence_ids=evidence_ids or [],
            confidence=confidence,
            status=TicketStatus.PENDING,
        )
        self._tickets[ticket.id] = ticket
        return ticket

    def get_ticket_sync(self, ticket_id: str) -> Optional[ApprovalTicket]:
        return self._tickets.get(ticket_id)

    def list_tickets_sync(
        self, status: Optional[TicketStatus] = None
    ) -> List[ApprovalTicket]:
        if status:
            return [t for t in self._tickets.values() if t.status == status]
        return list(self._tickets.values())

    async def get_ticket(self, ticket_id: str) -> Optional[ApprovalTicket]:
        return self.get_ticket_sync(ticket_id)

    async def list_tickets(
        self, status: Optional[TicketStatus] = None
    ) -> List[ApprovalTicket]:
        return self.list_tickets_sync(status)

    async def approve_and_execute(
        self, ticket_id: str, reviewed_by: str = "analyst"
    ) -> ApprovalTicket:
        """Approve an A1 ticket and trigger tool execution."""
        ticket = self._tickets.get(ticket_id)
        if not ticket:
            raise ValueError(f"Approval ticket {ticket_id} not found.")

        if ticket.status != TicketStatus.PENDING:
            raise ValueError(f"Ticket {ticket_id} is already in {ticket.status.value} state.")

        ticket.status = TicketStatus.APPROVED
        ticket.reviewed_at = datetime.now(timezone.utc)
        ticket.reviewed_by = reviewed_by

        if self._execution_callback:
            try:
                res = self._execution_callback(ticket.tool_name, ticket.arguments)
                if inspect.iscoroutine(res):
                    res = await res
                ticket.execution_result = res
                ticket.status = TicketStatus.EXECUTED
            except Exception as e:
                ticket.execution_result = {"error": str(e)}

        return ticket

    async def reject_ticket(
        self, ticket_id: str, rejection_reason: str, reviewed_by: str = "analyst"
    ) -> ApprovalTicket:
        """Reject an A1 ticket with an explanation."""
        ticket = self._tickets.get(ticket_id)
        if not ticket:
            raise ValueError(f"Approval ticket {ticket_id} not found.")

        if ticket.status != TicketStatus.PENDING:
            raise ValueError(f"Ticket {ticket_id} is already in {ticket.status.value} state.")

        ticket.status = TicketStatus.REJECTED
        ticket.reviewed_at = datetime.now(timezone.utc)
        ticket.reviewed_by = reviewed_by
        ticket.rejection_reason = rejection_reason
        return ticket


# Global inbox singleton
approval_inbox = ApprovalInbox()
