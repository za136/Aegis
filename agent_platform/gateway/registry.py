"""Tool Registry maintaining metadata, schemas, and typed execution handlers."""

import inspect
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel

from agent_platform.gateway.models import AutonomyLevel, ToolDefinition


class ToolRegistry:
    """Central registry of all tools available to agent squads."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._handlers: Dict[str, Callable] = {}

    def register(
        self,
        name: str,
        description: str,
        autonomy_level: Optional[AutonomyLevel] = None,
        is_write: bool = False,
        required_squad_roles: Optional[List[str]] = None,
        max_autonomous_amount: Optional[Decimal] = None,
        schema_model: Optional[type[BaseModel]] = None,
        min_autonomy: Optional[AutonomyLevel] = None,
        squad_permissions: Optional[List[str]] = None,
    ):
        """Decorator to register a typed tool execution handler."""
        resolved_autonomy = autonomy_level or min_autonomy
        if resolved_autonomy is None:
            resolved_autonomy = AutonomyLevel.A2_ACT_WITHIN_LIMITS
        resolved_roles = (
            required_squad_roles if required_squad_roles is not None else (squad_permissions or [])
        )

        def decorator(func: Callable):
            params_schema: Dict[str, Any] = {}
            if schema_model:
                params_schema = schema_model.model_json_schema()
            else:
                # Infer simple schema from signature
                sig = inspect.signature(func)
                properties = {}
                required = []
                for p_name, param in sig.parameters.items():
                    if p_name in ("self", "db", "context"):
                        continue
                    p_type = "string"
                    if param.annotation in (int, float, Decimal):
                        p_type = "number"
                    elif param.annotation is bool:
                        p_type = "boolean"
                    properties[p_name] = {"type": p_type, "description": f"Parameter {p_name}"}
                    if param.default == inspect.Parameter.empty:
                        required.append(p_name)
                params_schema = {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                }

            definition = ToolDefinition(
                name=name,
                description=description,
                autonomy_level=resolved_autonomy,
                required_squad_roles=resolved_roles,
                parameters_schema=params_schema,
                is_write=is_write,
                max_autonomous_amount=max_autonomous_amount,
            )
            self._tools[name] = definition
            self._handlers[name] = func
            return func

        return decorator

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def get_handler(self, name: str) -> Optional[Callable]:
        return self._handlers.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    def to_gemini_tools(self, squad_roles: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Export tool definitions to Google Gemini Function Declarations format."""
        gemini_tools = []
        for defn in self._tools.values():
            if squad_roles and defn.required_squad_roles:
                if not any(role in squad_roles for role in defn.required_squad_roles):
                    continue

            # Format for Google GenAI / Gemini FunctionCalling
            gemini_tools.append({
                "name": defn.name,
                "description": defn.description,
                "parameters": defn.parameters_schema,
            })
        return gemini_tools


# Global tool registry singleton
registry = ToolRegistry()
register_tool = registry.register
