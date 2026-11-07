"""FastAPI REST API Endpoints for Operations Copilot Squad."""

from fastapi import APIRouter
from agent_platform.squads.ops_copilot.copilot import OperationsCopilotAgent, ops_copilot
from agent_platform.squads.ops_copilot.models import CopilotAnswer, CopilotQueryRequest

router = APIRouter(prefix="/copilot", tags=["Operations Copilot Squad"])


@router.post("/ask", response_model=CopilotAnswer, summary="Ask Operations Copilot a natural language question")
async def ask_copilot(req: CopilotQueryRequest) -> CopilotAnswer:
    """Submit a question to the operations copilot and receive an evidence-grounded response with citations."""
    return await ops_copilot.answer(req)
