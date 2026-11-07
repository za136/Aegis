"""Model Context Protocol (MCP) JSON-RPC Endpoint for External Agent Tooling."""

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from agent_platform.gateway.executor import gateway_executor
from agent_platform.gateway.models import ToolInvocationRequest
from agent_platform.gateway.registry import registry

router = APIRouter(prefix="/mcp", tags=["Model Context Protocol (MCP)"])


class MCPJsonRpcRequest(BaseModel):
    """Standard JSON-RPC 2.0 Request for MCP."""
    jsonrpc: str = "2.0"
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    method: str
    params: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MCPJsonRpcResponse(BaseModel):
    """Standard JSON-RPC 2.0 Response for MCP."""
    jsonrpc: str = "2.0"
    id: Optional[str]
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


@router.post("", response_model=MCPJsonRpcResponse)
async def handle_mcp_jsonrpc(request: MCPJsonRpcRequest) -> MCPJsonRpcResponse:
    """Handle standard Model Context Protocol (MCP) JSON-RPC requests."""
    method = request.method
    params = request.params or {}

    # 1. Server Capabilities & Handshake
    if method == "initialize":
        return MCPJsonRpcResponse(
            id=request.id,
            result={
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": "aegis-mcp-gateway",
                    "version": "0.1.0",
                },
                "capabilities": {
                    "tools": {"listChanged": False},
                },
            },
        )

    # 2. List Tools
    if method == "tools/list":
        tools = registry.list_tools()
        tools_list = [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": t.parameters_schema,
                "metadata": {
                    "autonomy_level": t.autonomy_level.value,
                    "is_write": t.is_write,
                },
            }
            for t in tools
        ]
        return MCPJsonRpcResponse(id=request.id, result={"tools": tools_list})

    # 3. Call Tool
    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        if not tool_name:
            return MCPJsonRpcResponse(
                id=request.id,
                error={"code": -32602, "message": "Missing 'name' in tool call parameters"},
            )

        inv_req = ToolInvocationRequest(
            agent_id="mcp_external_agent",
            squad_name="payment_repair",
            tool_name=tool_name,
            arguments=arguments,
            reasoning=params.get("reasoning", "MCP external invocation"),
        )
        inv_res = await gateway_executor.invoke_tool(
            inv_req, squad_roles=["payment_repair", "financial_crime", "ops_analyst"]
        )

        if not inv_res.success:
            return MCPJsonRpcResponse(
                id=request.id,
                error={"code": -32000, "message": inv_res.error or "Tool execution failed"},
            )

        return MCPJsonRpcResponse(
            id=request.id,
            result={
                "content": [{"type": "text", "text": str(inv_res.data)}],
                "data": inv_res.data,
                "autonomy_level": inv_res.autonomy_level_applied.value,
                "approval_required": inv_res.approval_required,
                "approval_ticket_id": inv_res.approval_ticket_id,
            },
        )

    return MCPJsonRpcResponse(
        id=request.id,
        error={"code": -32601, "message": f"Method '{method}' not found"},
    )
