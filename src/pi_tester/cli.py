from __future__ import annotations

import argparse
from pathlib import Path

from .loader import load_suite, load_target
from .reporting import write_csv_report, write_html_report, write_json_report
from .runner import PromptInjectionRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pi-tester",
        description="Run systematic prompt injection tests against an LLM target adapter.",
    )
    parser.add_argument("--target", required=True, help="Path to target JSON config.")
    parser.add_argument("--suite", required=True, help="Path to test suite JSON.")
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Directory for generated JSON and HTML reports.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=1,
        help="Number of cases to execute concurrently.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    suite = load_suite(args.suite)
    target = load_target(args.target)
    run_result = PromptInjectionRunner(
        target=target,
        suite=suite,
        max_workers=args.max_workers,
    ).run()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = f"{target.name.lower().replace(' ', '_')}__{suite.name.lower().replace(' ', '_')}"
    json_path = write_json_report(run_result, output_dir / f"{slug}.json")
    html_path = write_html_report(run_result, output_dir / f"{slug}.html")
    csv_path = write_csv_report(run_result, output_dir / f"{slug}.csv")

    print(f"Target: {run_result.summary.target_name}")
    print(f"Suite: {run_result.summary.suite_name}")
    print(f"Passed: {run_result.summary.passed}/{run_result.summary.total}")
    print(f"Errored: {run_result.summary.errored}")
    print(f"Pass rate: {run_result.summary.pass_rate:.1f}%")
    print(f"Aggregate risk score: {run_result.summary.aggregate_risk_score}")
    print(f"Total runtime: {run_result.summary.total_duration_ms} ms")
    print(f"Verdict: {run_result.summary.verdict}")
    print(f"JSON report: {json_path}")
    print(f"HTML report: {html_path}")
    print(f"CSV report: {csv_path}")
