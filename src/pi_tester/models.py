from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CheckType(str, Enum):
    NONE_OF = "none_of"
    ANY_OF = "any_of"
    ALL_OF = "all_of"


@dataclass(slots=True)
class ResponseCheck:
    name: str
    type: CheckType
    patterns: list[str]
    description: str
    weight: int = 1


@dataclass(slots=True)
class InjectionCase:
    case_id: str
    title: str
    category: str
    severity: str
    prompt: str
    description: str
    checks: list[ResponseCheck] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    variant: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Suite:
    name: str
    description: str
    cases: list[InjectionCase]


@dataclass(slots=True)
class TargetSpec:
    name: str
    callable_path: str
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CheckResult:
    name: str
    passed: bool
    description: str
    matches: list[str]
    weight: int


@dataclass(slots=True)
class CaseResult:
    case: InjectionCase
    response_text: str
    check_results: list[CheckResult]
    passed: bool
    risk_score: int
    error_message: str | None = None
    duration_ms: int = 0


@dataclass(slots=True)
class RunSummary:
    suite_name: str
    target_name: str
    passed: int
    failed: int
    total: int
    max_risk_score: int
    aggregate_risk_score: int
    verdict: str
    errored: int
    pass_rate: float
    total_duration_ms: int
    average_duration_ms: float
    severity_breakdown: dict[str, int]
    category_breakdown: dict[str, int]


@dataclass(slots=True)
class RunResult:
    summary: RunSummary
    cases: list[CaseResult]
