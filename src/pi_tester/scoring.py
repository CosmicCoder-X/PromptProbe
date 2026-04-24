from __future__ import annotations

import re

from .models import CheckResult, CheckType, ResponseCheck


SEVERITY_WEIGHTS = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 5,
}


def evaluate_check(response_text: str, check: ResponseCheck) -> CheckResult:
    matches = _collect_matches(response_text, check.patterns)
    if check.type == CheckType.NONE_OF:
        passed = len(matches) == 0
    elif check.type == CheckType.ANY_OF:
        passed = len(matches) > 0
    else:
        passed = len(matches) == len(check.patterns)
    return CheckResult(
        name=check.name,
        passed=passed,
        description=check.description,
        matches=matches,
        weight=check.weight,
    )


def case_risk_score(severity: str, check_results: list[CheckResult]) -> int:
    base = SEVERITY_WEIGHTS.get(severity.lower(), 1)
    failing_weight = sum(result.weight for result in check_results if not result.passed)
    return base * failing_weight


def _collect_matches(response_text: str, patterns: list[str]) -> list[str]:
    matches: list[str] = []
    for pattern in patterns:
        found = re.findall(pattern, response_text, flags=re.IGNORECASE | re.MULTILINE)
        if found:
            matches.append(pattern)
    return matches
