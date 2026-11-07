"""Admin Kill Switches and Dynamic Autonomy Controls for Agent Platform."""

from decimal import Decimal
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from agent_platform.gateway.models import AutonomyLevel


class KillSwitchAuditEntry(BaseModel):
    timestamp: float
    action: str
    target: str
    operator_id: str
    details: str


class KillSwitchState(BaseModel):
    global_emergency_stop: bool = False
    emergency_stop_reason: Optional[str] = None
    squad_status: Dict[str, bool] = Field(
        default_factory=lambda: {
            "payment_repair": True,
            "onboarding": True,
            "aegis": True,
            "reconciliation": True,
            "support_disputes": True,
            "ops_copilot": True,
        }
    )
    squad_autonomy_ceilings: Dict[str, AutonomyLevel] = Field(
        default_factory=lambda: {
            "payment_repair": AutonomyLevel.A2_ACT_WITHIN_LIMITS,
            "onboarding": AutonomyLevel.A2_ACT_WITHIN_LIMITS,
            "aegis": AutonomyLevel.A1_ACT_WITH_APPROVAL,
            "reconciliation": AutonomyLevel.A2_ACT_WITHIN_LIMITS,
            "support_disputes": AutonomyLevel.A1_ACT_WITH_APPROVAL,
            "ops_copilot": AutonomyLevel.A2_ACT_WITHIN_LIMITS,
        }
    )
    financial_limits: Dict[str, Decimal] = Field(
        default_factory=lambda: {
            "max_autonomous_transfer_usd": Decimal("100.00"),
            "repair_auto_threshold_usd": Decimal("250.00"),
            "provisional_credit_auto_usd": Decimal("50.00"),
        }
    )


class KillSwitchManager:
    """Manages emergency stop kill switches, per-squad pauses, and dynamic autonomy limits."""

    def __init__(self):
        self.state = KillSwitchState()
        self.audit_log: list[KillSwitchAuditEntry] = []

    def engage_global_kill_switch(self, reason: str, operator_id: str = "op_admin"):
        """Activate the global emergency stop halting all agent tool executions immediately."""
        import time
        self.state.global_emergency_stop = True
        self.state.emergency_stop_reason = reason
        self.audit_log.append(
            KillSwitchAuditEntry(
                timestamp=time.time(),
                action="ENGAGE_GLOBAL_STOP",
                target="ALL_SQUADS",
                operator_id=operator_id,
                details=reason,
            )
        )

    def disengage_global_kill_switch(self, operator_id: str = "op_admin"):
        """Deactivate global emergency stop and restore normal operations."""
        import time
        self.state.global_emergency_stop = False
        self.state.emergency_stop_reason = None
        self.audit_log.append(
            KillSwitchAuditEntry(
                timestamp=time.time(),
                action="DISENGAGE_GLOBAL_STOP",
                target="ALL_SQUADS",
                operator_id=operator_id,
                details="Normal platform operations restored.",
            )
        )

    def set_squad_state(self, squad_name: str, enabled: bool, operator_id: str = "op_admin"):
        """Enable or disable an individual squad at runtime."""
        import time
        self.state.squad_status[squad_name] = enabled
        self.audit_log.append(
            KillSwitchAuditEntry(
                timestamp=time.time(),
                action="ENABLE_SQUAD" if enabled else "DISABLE_SQUAD",
                target=squad_name,
                operator_id=operator_id,
                details=f"Squad '{squad_name}' set to enabled={enabled}.",
            )
        )

    def set_squad_autonomy_ceiling(self, squad_name: str, ceiling: AutonomyLevel, operator_id: str = "op_admin"):
        """Dynamically cap the maximum autonomy level an agent squad is permitted to execute."""
        import time
        self.state.squad_autonomy_ceilings[squad_name] = ceiling
        self.audit_log.append(
            KillSwitchAuditEntry(
                timestamp=time.time(),
                action="SET_AUTONOMY_CEILING",
                target=squad_name,
                operator_id=operator_id,
                details=f"Squad '{squad_name}' max autonomy clamped to {ceiling.value}.",
            )
        )

    def set_financial_limit(self, limit_key: str, amount_usd: Decimal, operator_id: str = "op_admin"):
        """Adjust financial autonomy thresholds at runtime."""
        import time
        self.state.financial_limits[limit_key] = amount_usd
        self.audit_log.append(
            KillSwitchAuditEntry(
                timestamp=time.time(),
                action="SET_FINANCIAL_LIMIT",
                target=limit_key,
                operator_id=operator_id,
                details=f"Limit '{limit_key}' updated to ${amount_usd}.",
            )
        )

    def is_squad_enabled(self, squad_name: str) -> bool:
        """Check if a squad is permitted to execute tools."""
        if self.state.global_emergency_stop:
            return False
        return self.state.squad_status.get(squad_name, True)

    def get_effective_autonomy(self, squad_name: str, requested_level: AutonomyLevel) -> AutonomyLevel:
        """Enforce dynamic autonomy ceilings: requested level cannot exceed ceiling."""
        if self.state.global_emergency_stop:
            return AutonomyLevel.A0_SUGGEST

        ceiling = self.state.squad_autonomy_ceilings.get(squad_name, AutonomyLevel.A3_FULLY_AUTONOMOUS)

        hierarchy = {
            AutonomyLevel.A0_SUGGEST: 0,
            AutonomyLevel.A1_ACT_WITH_APPROVAL: 1,
            AutonomyLevel.A2_ACT_WITHIN_LIMITS: 2,
            AutonomyLevel.A3_FULLY_AUTONOMOUS: 3,
        }

        if hierarchy[requested_level] > hierarchy[ceiling]:
            return ceiling
        return requested_level

    def get_limit(self, limit_key: str, default_val: Decimal) -> Decimal:
        """Retrieve dynamic financial limit or fallback to default."""
        return self.state.financial_limits.get(limit_key, default_val)

    def get_status_overview(self) -> Dict[str, Any]:
        """Summary of current kill switches, limits, and squad statuses."""
        return {
            "global_emergency_stop": self.state.global_emergency_stop,
            "emergency_stop_reason": self.state.emergency_stop_reason,
            "squads": self.state.squad_status,
            "autonomy_ceilings": {k: v.value for k, v in self.state.squad_autonomy_ceilings.items()},
            "financial_limits": {k: str(v) for k, v in self.state.financial_limits.items()},
            "audit_log_count": len(self.audit_log),
        }


# Global kill switch singleton
kill_switch = KillSwitchManager()
