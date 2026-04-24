from __future__ import annotations

from dataclasses import asdict
import csv
import html
import json
from pathlib import Path

from .models import RunResult


def write_json_report(run_result: RunResult, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.write_text(
        json.dumps(_serialize(run_result), indent=2),
        encoding="utf-8",
    )
    return path


def write_html_report(run_result: RunResult, output_path: str | Path) -> Path:
    summary = run_result.summary
    rows = []
    for case_result in run_result.cases:
        response_markup = html.escape(case_result.response_text) if case_result.response_text else "No response body captured."
        error_markup = (
            f"<p class='error'>Error: {html.escape(case_result.error_message)}</p>"
            if case_result.error_message
            else ""
        )
        check_markup = "".join(
            (
                "<li>"
                f"<strong>{html.escape(check.name)}</strong>: "
                f"{'PASS' if check.passed else 'FAIL'}"
                f" - {html.escape(check.description)}"
                f"{_match_suffix(check.matches)}"
                "</li>"
            )
            for check in case_result.check_results
        )
        rows.append(
            "<tr>"
            f"<td>{html.escape(case_result.case.case_id)}</td>"
            f"<td>{html.escape(case_result.case.title)}</td>"
            f"<td>{html.escape(case_result.case.severity.upper())}</td>"
            f"<td>{'PASS' if case_result.passed else 'FAIL'}</td>"
            f"<td>{case_result.risk_score}</td>"
            f"<td>{case_result.duration_ms} ms</td>"
            f"<td><details><summary>Response</summary>{error_markup}<pre>{response_markup}</pre></details></td>"
            f"<td><ul>{check_markup}</ul></td>"
            "</tr>"
        )

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Prompt Injection Report</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f4efe7;
      --surface: #fffdf8;
      --ink: #172121;
      --muted: #5c6b73;
      --accent: #9c3d10;
      --ok: #1f7a4d;
      --bad: #a61e4d;
      --warn: #9a6700;
      --border: #dfd5c7;
    }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top right, rgba(156, 61, 16, 0.10), transparent 30%),
        linear-gradient(180deg, #f6f1ea 0%, var(--bg) 100%);
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    .hero, table {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 18px;
      box-shadow: 0 12px 32px rgba(23, 33, 33, 0.07);
    }}
    .hero {{
      padding: 24px;
      margin-bottom: 24px;
    }}
    .meta {{
      display: flex;
      gap: 18px;
      flex-wrap: wrap;
      color: var(--muted);
    }}
    .score {{
      font-size: 2.6rem;
      color: var(--accent);
      margin: 8px 0;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      overflow: hidden;
    }}
    th, td {{
      text-align: left;
      vertical-align: top;
      padding: 14px;
      border-bottom: 1px solid var(--border);
      font-size: 0.95rem;
    }}
    th {{
      background: #f8f3eb;
    }}
    pre {{
      white-space: pre-wrap;
      margin: 8px 0 0;
    }}
    .pass {{ color: var(--ok); }}
    .fail {{ color: var(--bad); }}
    .error {{ color: var(--warn); font-weight: bold; }}
    .chips {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 18px;
    }}
    .chip {{
      padding: 8px 12px;
      border-radius: 999px;
      background: #f8f3eb;
      border: 1px solid var(--border);
      color: var(--muted);
      font-size: 0.9rem;
    }}
    ul {{
      margin: 0;
      padding-left: 18px;
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <p>LLM Prompt Injection Tester</p>
      <h1>{html.escape(summary.target_name)} vs {html.escape(summary.suite_name)}</h1>
      <p>{html.escape(summary.verdict)}</p>
      <p class="score">Aggregate risk score: {summary.aggregate_risk_score}</p>
      <div class="meta">
        <span>Passed: {summary.passed}</span>
        <span>Failed: {summary.failed}</span>
        <span>Errored: {summary.errored}</span>
        <span>Total: {summary.total}</span>
        <span>Pass rate: {summary.pass_rate:.1f}%</span>
        <span>Total runtime: {summary.total_duration_ms} ms</span>
        <span>Max single-case risk: {summary.max_risk_score}</span>
      </div>
      <div class="chips">
        {''.join(f"<span class='chip'>severity {html.escape(key)}: {value}</span>" for key, value in summary.severity_breakdown.items())}
        {''.join(f"<span class='chip'>category {html.escape(key)}: {value}</span>" for key, value in summary.category_breakdown.items())}
      </div>
    </section>
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Case</th>
          <th>Severity</th>
          <th>Result</th>
          <th>Risk</th>
          <th>Latency</th>
          <th>Response</th>
          <th>Checks</th>
        </tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
  </main>
</body>
</html>
"""
    path = Path(output_path)
    path.write_text(html_doc, encoding="utf-8")
    return path


def _serialize(run_result: RunResult) -> dict:
    return {
        "summary": asdict(run_result.summary),
        "cases": [
            {
                "case": {
                    "case_id": case_result.case.case_id,
                    "title": case_result.case.title,
                    "category": case_result.case.category,
                    "severity": case_result.case.severity,
                    "prompt": case_result.case.prompt,
                    "description": case_result.case.description,
                    "tags": case_result.case.tags,
                    "metadata": case_result.case.metadata,
                    "variant": case_result.case.variant,
                },
                "response_text": case_result.response_text,
                "passed": case_result.passed,
                "risk_score": case_result.risk_score,
                "error_message": case_result.error_message,
                "duration_ms": case_result.duration_ms,
                "check_results": [asdict(check) for check in case_result.check_results],
            }
            for case_result in run_result.cases
        ],
    }


def _match_suffix(matches: list[str]) -> str:
    if not matches:
        return ""
    return " | matched patterns: " + ", ".join(html.escape(match) for match in matches)


def write_csv_report(run_result: RunResult, output_path: str | Path) -> Path:
    path = Path(output_path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "case_id",
                "title",
                "category",
                "severity",
                "passed",
                "risk_score",
                "duration_ms",
                "error_message",
                "matched_patterns",
                "response_text",
            ]
        )
        for case_result in run_result.cases:
            matched_patterns = sorted(
                {
                    pattern
                    for check in case_result.check_results
                    for pattern in check.matches
                }
            )
            writer.writerow(
                [
                    case_result.case.case_id,
                    case_result.case.title,
                    case_result.case.category,
                    case_result.case.severity,
                    case_result.passed,
                    case_result.risk_score,
                    case_result.duration_ms,
                    case_result.error_message or "",
                    "; ".join(matched_patterns),
                    case_result.response_text,
                ]
            )
    return path
