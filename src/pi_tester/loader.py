from __future__ import annotations

from itertools import product
import importlib
import json
from pathlib import Path

from .models import CheckType, InjectionCase, ResponseCheck, Suite, TargetSpec


def load_suite(path: str | Path) -> Suite:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    cases: list[InjectionCase] = []
    for item in raw["cases"]:
        cases.extend(_expand_case(item))
    return Suite(
        name=raw["name"],
        description=raw["description"],
        cases=cases,
    )


def load_target(path: str | Path) -> TargetSpec:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return TargetSpec(
        name=raw["name"],
        callable_path=raw["callable"],
        description=raw["description"],
        metadata=raw.get("metadata", {}),
    )


def resolve_callable(callable_path: str):
    module_name, function_name = callable_path.split(":", maxsplit=1)
    module = importlib.import_module(module_name)
    return getattr(module, function_name)


def _expand_case(item: dict) -> list[InjectionCase]:
    variants = _build_variants(item)
    expanded_cases: list[InjectionCase] = []
    for index, variant in enumerate(variants, start=1):
        checks = [
            ResponseCheck(
                name=_render_template(check["name"], variant),
                type=CheckType(check["type"]),
                patterns=[_render_template(pattern, variant) for pattern in check["patterns"]],
                description=_render_template(check["description"], variant),
                weight=check.get("weight", 1),
            )
            for check in item.get("checks", [])
        ]
        case_id = item["case_id"]
        if len(variants) > 1:
            case_id = f"{case_id}-{index:02d}"
        expanded_cases.append(
            InjectionCase(
                case_id=case_id,
                title=_render_template(item["title"], variant),
                category=item["category"],
                severity=item["severity"],
                prompt=_render_template(_resolve_prompt(item), variant),
                description=_render_template(item["description"], variant),
                checks=checks,
                tags=[_render_template(tag, variant) for tag in item.get("tags", [])],
                metadata=item.get("metadata", {}),
                variant=variant,
            )
        )
    return expanded_cases


def _build_variants(item: dict) -> list[dict]:
    if "matrix" not in item:
        return [dict(item.get("variant", {}))]
    matrix = item["matrix"]
    if not matrix:
        return [dict(item.get("variant", {}))]
    keys = list(matrix.keys())
    combinations = []
    for values in product(*(matrix[key] for key in keys)):
        variant = dict(item.get("variant", {}))
        variant.update(dict(zip(keys, values)))
        combinations.append(variant)
    return combinations


def _render_template(value: str, variant: dict) -> str:
    if not variant:
        return value
    return value.format_map(_SafeFormatDict(variant))


def _resolve_prompt(item: dict) -> str:
    if "prompt_template" in item:
        return item["prompt_template"]
    return item["prompt"]


class _SafeFormatDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"
