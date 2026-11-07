"""Unit and Integration Tests for Platform Infrastructure, Helm, Terraform, GitOps, and Telemetry."""

import json
from pathlib import Path
import pytest
import yaml

from services.common.telemetry import (
    MetricCounter,
    PlatformMetrics,
    TelemetryTracer,
    metrics,
    tracer,
)


def test_metric_counter_behavior():
    """Verify Prometheus MetricCounter label tracking and value incrementation."""
    counter = MetricCounter(
        name="test_counter_total",
        description="Test metric counter description",
    )
    assert counter.name == "test_counter_total"
    assert counter.get(status="success") == 0

    counter.inc(1, status="success", squad="payment_repair")
    counter.inc(2, status="success", squad="payment_repair")
    counter.inc(1, status="error", squad="payment_repair")

    assert counter.get(squad="payment_repair", status="success") == 3
    assert counter.get(squad="payment_repair", status="error") == 1
    assert counter.get(status="unknown") == 0


def test_platform_metrics_export_prometheus_format():
    """Verify Prometheus text format generation conforms to Prometheus standards."""
    test_metrics = PlatformMetrics()
    test_metrics.payments_processed.inc(5)
    test_metrics.holds_reserved.inc(3)
    test_metrics.tool_invocations.inc(2, tool="get_payment_details", autonomy="A2")
    test_metrics.approval_tickets.inc(1, squad="aegis")
    test_metrics.guardrail_triggers.inc(1)
    test_metrics.verifier_rejections.inc(0)

    prom_text = test_metrics.export_prometheus_text()
    assert "# HELP meridian_payments_processed_total" in prom_text
    assert "# TYPE meridian_payments_processed_total counter" in prom_text
    assert "meridian_payments_processed_total 5" in prom_text
    assert "meridian_ledger_holds_reserved_total 3" in prom_text
    assert 'aegis_tool_gateway_invocations_total{autonomy=A2,tool=get_payment_details} 2' in prom_text
    assert 'aegis_maker_checker_tickets_total{squad=aegis} 1' in prom_text
    assert "aegis_guardrail_injection_triggers_total 1" in prom_text


def test_telemetry_span_tracer():
    """Verify distributed span tracing lifecycle, IDs, and duration recording."""
    test_tracer = TelemetryTracer()
    with test_tracer.start_span("agent_step", squad="onboarding", action="extract_docs") as span:
        assert span.name == "agent_step"
        assert len(span.span_id) == 16
        assert len(span.trace_id) == 32
        assert span.attributes["squad"] == "onboarding"
        assert span.attributes["action"] == "extract_docs"
        assert span.start_time > 0
        assert span.end_time is None

    # After exiting context, span should be finalized in completed_spans
    assert len(test_tracer.completed_spans) == 1
    completed = test_tracer.completed_spans[0]
    assert completed.end_time is not None
    assert completed.end_time >= completed.start_time
    assert len(test_tracer.active_spans) == 0


def test_helm_chart_structure():
    """Verify Helm chart manifests exist and have valid YAML syntax and configurations."""
    base_dir = Path("/home/zabedin/projects/Aegis/infra/helm/aegis-platform")
    chart_file = base_dir / "Chart.yaml"
    values_file = base_dir / "values.yaml"
    templates_dir = base_dir / "templates"

    assert chart_file.exists(), "Chart.yaml must exist"
    assert values_file.exists(), "values.yaml must exist"

    chart_meta = yaml.safe_load(chart_file.read_text())
    assert chart_meta["name"] == "aegis-platform"
    assert chart_meta["version"] == "0.1.0"
    assert "gemini" in chart_meta["keywords"]

    values = yaml.safe_load(values_file.read_text())
    assert values["namespaces"]["core"] == "meridian-core"
    assert values["namespaces"]["agents"] == "meridian-agent-platform"
    assert values["apiGateway"]["env"]["GEMINI_MODEL"] == "gemini-3.8-flash"
    assert values["networkPolicy"]["enabled"] is True

    # Check key templates exist
    assert (templates_dir / "namespaces.yaml").exists()
    assert (templates_dir / "networkpolicies.yaml").exists()
    assert (templates_dir / "api-gateway.yaml").exists()
    assert (templates_dir / "customer-portal.yaml").exists()
    assert (templates_dir / "ops-console.yaml").exists()
    assert (templates_dir / "ingress.yaml").exists()


def test_network_policy_least_privilege_egress():
    """Verify NetworkPolicy defines strict egress rules restricting agent traffic to HTTPS and Core."""
    np_file = Path("/home/zabedin/projects/Aegis/infra/helm/aegis-platform/templates/networkpolicies.yaml")
    content = np_file.read_text()

    # Agent platform egress should permit DNS (53), HTTPS (443) for Gemini API, and Core API Gateway (8000)
    assert "agent-platform-egress-boundary" in content
    assert "port: 443" in content
    assert "port: 8000" in content
    assert "port: 53" in content
    # Core DB ingress isolation should restrict postgres access
    assert "core-ledger-ingress-isolation" in content
    assert "port: 5432" in content


def test_terraform_iac_configuration():
    """Verify Terraform configuration files contain required providers, variables, and outputs."""
    tf_dir = Path("/home/zabedin/projects/Aegis/infra/terraform")
    main_tf = (tf_dir / "main.tf").read_text()
    vars_tf = (tf_dir / "variables.tf").read_text()
    outputs_tf = (tf_dir / "outputs.tf").read_text()

    assert "required_version" in main_tf
    assert "helm_release" in main_tf
    assert "kubernetes_secret" in main_tf

    assert 'variable "environment"' in vars_tf
    assert 'variable "cluster_name"' in vars_tf
    assert 'variable "postgres_instance_class"' in vars_tf

    assert "api_gateway_endpoint" in outputs_tf
    assert "ops_console_endpoint" in outputs_tf
    assert "customer_portal_endpoint" in outputs_tf


def test_gitops_argo_cd_definitions():
    """Verify Argo CD Application and Rollout specs for progressive delivery."""
    gitops_dir = Path("/home/zabedin/projects/Aegis/infra/gitops")
    app_root = (gitops_dir / "application-root.yaml").read_text()
    canary = (gitops_dir / "canary-rollout.yaml").read_text()

    assert "kind: Application" in app_root
    assert "aegis-meridian-platform" in app_root
    assert "selfHeal: true" in app_root

    assert "kind: Rollout" in canary
    assert "api-gateway-canary" in canary
    assert "setWeight: 10" in canary
    assert "setWeight: 25" in canary


def test_grafana_dashboard_json_validity():
    """Verify Grafana telemetry dashboard definition is valid JSON with required platform metrics."""
    dash_file = Path("/home/zabedin/projects/Aegis/infra/telemetry/dashboards/aegis-overview.json")
    assert dash_file.exists()

    data = json.loads(dash_file.read_text())
    assert data["title"] == "Aegis & Meridian Platform Executive Overview"
    targets = [target["expr"] for p in data["panels"] for target in p.get("targets", [])]
    assert any("meridian_payments_processed_total" in t for t in targets)
    assert any("aegis_tool_gateway_invocations_total" in t for t in targets)
    assert any("aegis_guardrail_injection_triggers_total" in t for t in targets)
    assert any("aegis_verifier_rejections_total" in t for t in targets)
