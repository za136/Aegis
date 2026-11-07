"""Continuous Integration (CI) Evaluation Gates and Regression Blocker."""

import asyncio
from typing import Dict
from evals.harness.runner import FullEvaluationReport, runner


class CIRegressionError(Exception):
    """Raised when evaluation metrics fail to meet mandatory CI release thresholds."""
    pass


class CIReleaseGate:
    """Enforces non-negotiable safety, accuracy, and latency thresholds before release."""

    def __init__(self, benchmark_runner=None):
        self.runner = benchmark_runner or runner

    async def verify_ci_gates(self) -> FullEvaluationReport:
        """Run all benchmarks and assert passing gate thresholds."""
        report = await self.runner.run_full_evaluation()

        failed_gates = [gate for gate, passed in report.gate_checks.items() if not passed]
        if failed_gates:
            raise CIRegressionError(
                f"CI Gate Check FAILED for {len(failed_gates)} criterion/criteria: {', '.join(failed_gates)}. "
                "Deployment blocked."
            )

        return report

    def format_markdown_report(self, report: FullEvaluationReport) -> str:
        """Format an evaluation report as a GitHub-flavored Markdown table for CI logs and artifacts."""
        md = []
        md.append("# 🛡️ Aegis Platform CI Evaluation & Regression Gate Report")
        md.append(f"**Timestamp**: `{report.timestamp}`  ")
        md.append(f"**Status**: {'✅ PASSED (Ready for Deployment)' if report.overall_passed else '❌ FAILED'}\n")
        md.append("## Release Gate Verification Matrix")
        md.append("| Gate Name | Target Threshold | Measured Result | Status |")
        md.append("| :--- | :--- | :--- | :--- |")

        gates_info = [
            ("Financial Crime False Negative Rate", "0.0%", f"{report.financial_crime_metrics.false_negative_rate:.1%}", report.gate_checks["financial_crime_fnr_zero"]),
            ("Onboarding False Negative Rate", "0.0%", f"{report.onboarding_metrics.false_negative_rate:.1%}", report.gate_checks["onboarding_fnr_zero"]),
            ("Prompt Injection Attack Success Rate", "0.0%", f"{report.safety_metrics.attack_success_rate:.1%}", report.gate_checks["prompt_injection_asr_zero"]),
            ("SAR Narrative Unsupported Claim Rate", "0.0%", f"{report.faithfulness_metrics.unsupported_claim_rate:.1%}", report.gate_checks["unsupported_claim_rate_zero"]),
            ("Payment Exception Repair Accuracy", ">= 95.0%", f"{report.payment_repair_metrics.accuracy:.1%}", report.gate_checks["payment_repair_accuracy_gte_95"]),
            ("Trajectory Step Budget Breaches", "0.0%", f"{report.trajectory_metrics.step_budget_breach_rate:.1%}", report.gate_checks["step_budget_breach_rate_zero"]),
        ]

        for name, target, actual, status_ok in gates_info:
            icon = "✅ PASS" if status_ok else "❌ FAIL"
            md.append(f"| {name} | `{target}` | `{actual}` | {icon} |")

        md.append("\n## Squad Benchmarks Summary")
        md.append(f"- **Payment Exception Repair**: Accuracy = `{report.payment_repair_metrics.accuracy:.1%}` ({report.payment_repair_metrics.notes})")
        md.append(f"- **Onboarding & KYC**: Precision = `{report.onboarding_metrics.precision:.1%}`, Recall = `{report.onboarding_metrics.recall:.1%}`, F1 = `{report.onboarding_metrics.f1_score:.3f}`")
        md.append(f"- **Aegis Financial Crime**: Precision = `{report.financial_crime_metrics.precision:.1%}`, Recall = `{report.financial_crime_metrics.recall:.1%}`, FNR = `{report.financial_crime_metrics.false_negative_rate:.1%}`")
        md.append(f"- **Adversarial Security**: Tested `{report.safety_metrics.total_attacks_tested}` attacks, `{report.safety_metrics.attacks_blocked_count}` blocked, ASR = `{report.safety_metrics.attack_success_rate:.1%}`")
        md.append(f"- **Evidence Faithfulness**: Evaluated `{report.faithfulness_metrics.total_narratives_evaluated}` narratives, `{report.faithfulness_metrics.average_citations_per_narrative}` avg citations/case, Unsupported Rate = `{report.faithfulness_metrics.unsupported_claim_rate:.1%}`")
        md.append(f"- **Trajectory Efficiency**: Avg steps/case = `{report.trajectory_metrics.average_steps_per_case}`, Breaches = `{report.trajectory_metrics.step_budget_breaches_count}`")

        return "\n".join(md)


ci_gate = CIReleaseGate()
