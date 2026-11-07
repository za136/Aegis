"""Command-Line Interface (CLI) for running evaluation benchmarks and CI release gates."""

import argparse
import asyncio
import sys

from evals.ci.gate import ci_gate
from evals.harness.runner import runner


async def main_async():
    parser = argparse.ArgumentParser(description="Aegis / Meridian Evaluation Benchmark Runner & CI Gate")
    parser.add_argument("--gate", action="store_true", help="Assert mandatory CI release gates and fail if any threshold regresses")
    parser.add_argument("--json", action="store_true", help="Output full report as JSON")
    args = parser.parse_args()

    print("🚀 Running Aegis Platform Evaluation Benchmark Suite...")

    if args.gate:
        try:
            report = await ci_gate.verify_ci_gates()
            print("\n" + ci_gate.format_markdown_report(report))
            print("\n🎉 ALL CI RELEASE GATES PASSED! Ready for deployment.")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ RELEASE GATE FAILED: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        report = await runner.run_full_evaluation()
        if args.json:
            print(report.model_dump_json(indent=2))
        else:
            print("\n" + ci_gate.format_markdown_report(report))


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
