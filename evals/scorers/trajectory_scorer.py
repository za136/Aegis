"""Agent Trajectory, Step Budget, and Tool Call Efficiency Scorer."""

from typing import Any, Dict, List
from pydantic import BaseModel


class TrajectoryMetrics(BaseModel):
    total_runs_evaluated: int
    average_steps_per_case: float
    max_steps_observed: int
    step_budget_breaches_count: int
    step_budget_breach_rate: float
    redundant_tool_call_rate: float


def compute_trajectory_metrics(
    runs: List[Dict[str, Any]], max_step_budget: int = 5
) -> TrajectoryMetrics:
    """Evaluate trajectory efficiency and step budget adherence."""
    if not runs:
        return TrajectoryMetrics(
            total_runs_evaluated=0,
            average_steps_per_case=0.0,
            max_steps_observed=0,
            step_budget_breaches_count=0,
            step_budget_breach_rate=0.0,
            redundant_tool_call_rate=0.0,
        )

    total_steps = 0
    max_steps = 0
    breaches = 0
    total_redundant = 0
    total_tool_calls = 0

    for r in runs:
        steps = r.get("steps_taken", 1)
        total_steps += steps
        if steps > max_steps:
            max_steps = steps
        if steps > max_step_budget:
            breaches += 1

        tool_calls = r.get("tool_calls", [])
        total_tool_calls += len(tool_calls)
        seen = set()
        for call in tool_calls:
            name = call if isinstance(call, str) else call.get("name", "")
            if name in seen:
                total_redundant += 1
            seen.add(name)

    total = len(runs)
    avg_steps = round(total_steps / total, 2)
    breach_rate = round(breaches / total, 4)
    redundant_rate = (
        round(total_redundant / total_tool_calls, 4) if total_tool_calls > 0 else 0.0
    )

    return TrajectoryMetrics(
        total_runs_evaluated=total,
        average_steps_per_case=avg_steps,
        max_steps_observed=max_steps,
        step_budget_breaches_count=breaches,
        step_budget_breach_rate=breach_rate,
        redundant_tool_call_rate=redundant_rate,
    )
