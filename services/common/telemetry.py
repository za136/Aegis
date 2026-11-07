"""OpenTelemetry Distributed Tracing and Prometheus Observability Metrics."""

import time
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional
from pydantic import BaseModel, Field


class MetricCounter(BaseModel):
    name: str
    description: str
    counts: Dict[str, int] = Field(default_factory=dict)

    def inc(self, amount: int = 1, **labels):
        label_key = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        self.counts[label_key] = self.counts.get(label_key, 0) + amount

    def get(self, **labels) -> int:
        label_key = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return self.counts.get(label_key, 0)


class PlatformMetrics:
    """Prometheus & OpenTelemetry runtime platform metrics tracker."""

    def __init__(self):
        # 1. Banking & Payment Metrics
        self.payments_processed = MetricCounter(
            name="meridian_payments_processed_total",
            description="Total count of payment instructions processed through the saga",
        )
        self.holds_reserved = MetricCounter(
            name="meridian_ledger_holds_reserved_total",
            description="Total two-phase funds reservations placed on ledger",
        )

        # 2. Agent Platform & Tool Gateway Metrics
        self.tool_invocations = MetricCounter(
            name="aegis_tool_gateway_invocations_total",
            description="Total tool executions routed through the MCP gateway",
        )
        self.approval_tickets = MetricCounter(
            name="aegis_maker_checker_tickets_total",
            description="Count of A1 human-in-the-loop approval tickets created",
        )

        # 3. Security & Safety Metrics
        self.guardrail_triggers = MetricCounter(
            name="aegis_guardrail_injection_triggers_total",
            description="Count of adversarial prompt injection attempts intercepted",
        )
        self.verifier_rejections = MetricCounter(
            name="aegis_verifier_rejections_total",
            description="Count of SAR narratives rejected for unevidenced claims",
        )

    def export_prometheus_text(self) -> str:
        """Export metrics formatted in Prometheus text format."""
        lines = []
        for metric in [
            self.payments_processed,
            self.holds_reserved,
            self.tool_invocations,
            self.approval_tickets,
            self.guardrail_triggers,
            self.verifier_rejections,
        ]:
            lines.append(f"# HELP {metric.name} {metric.description}")
            lines.append(f"# TYPE {metric.name} counter")
            if not metric.counts:
                lines.append(f"{metric.name} 0")
            for label_str, val in metric.counts.items():
                if label_str:
                    lines.append(f"{metric.name}{{{label_str}}} {val}")
                else:
                    lines.append(f"{metric.name} {val}")
        return "\n".join(lines) + "\n"


class SpanRecord(BaseModel):
    span_id: str
    trace_id: str
    name: str
    start_time: float
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class TelemetryTracer:
    """Lightweight in-process OpenTelemetry-compatible span tracer."""

    def __init__(self):
        self.active_spans: Dict[str, SpanRecord] = {}
        self.completed_spans: list[SpanRecord] = []

    @contextmanager
    def start_span(
        self, name: str, trace_id: Optional[str] = None, **attributes
    ) -> Generator[SpanRecord, None, None]:
        import uuid
        t_id = trace_id or uuid.uuid4().hex
        s_id = uuid.uuid4().hex[:16]

        span = SpanRecord(
            span_id=s_id,
            trace_id=t_id,
            name=name,
            start_time=time.time(),
            attributes=attributes,
        )
        self.active_spans[s_id] = span
        try:
            yield span
        finally:
            span.end_time = time.time()
            self.active_spans.pop(s_id, None)
            self.completed_spans.append(span)


# Global telemetry singletons
metrics = PlatformMetrics()
tracer = TelemetryTracer()
