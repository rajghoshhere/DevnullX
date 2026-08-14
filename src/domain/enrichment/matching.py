from __future__ import annotations

import re
from typing import Any

_NON_ALNUM = re.compile(r"[^A-Z0-9]+")


def normalize_label(value: str) -> str:
    return " ".join(_NON_ALNUM.sub(" ", value.upper()).split())


def match_alias(raw_value: str, aliases: dict[str, list[str]]) -> tuple[str, float] | None:
    normalized_input = normalize_label(raw_value)
    if not normalized_input:
        return None

    exact_hits: list[tuple[int, str]] = []
    contains_hits: list[tuple[int, str]] = []
    for code, alias_values in aliases.items():
        for alias in alias_values:
            normalized_alias = normalize_label(str(alias))
            if not normalized_alias:
                continue
            if normalized_input == normalized_alias:
                exact_hits.append((len(normalized_alias), code))
            elif _contains_alias(normalized_input, normalized_alias):
                contains_hits.append((len(normalized_alias), code))

    if exact_hits:
        exact_hits.sort(reverse=True)
        return exact_hits[0][1], 1.0
    if contains_hits:
        contains_hits.sort(reverse=True)
        return contains_hits[0][1], 0.9
    return None


def _contains_alias(haystack: str, alias: str) -> bool:
    pattern = rf"(?:^| ){re.escape(alias)}(?:$| )"
    return re.search(pattern, haystack) is not None


def select_threshold_code(value: int, bands: list[dict[str, Any]]) -> str | None:
    for band in bands:
        max_inclusive = band.get("max_inclusive")
        code = str(band["code"])
        if max_inclusive is None:
            return code
        if value <= int(max_inclusive):
            return code
    return None
