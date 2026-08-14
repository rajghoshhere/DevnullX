from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from domain.enrichment.matching import match_alias, select_threshold_code
from domain.enrichment.models import (
    SOURCE_DERIVED,
    SOURCE_SYSTEM_RULE_ENGINE,
    AttributeProvenance,
    Rule,
    RuleResult,
    VehicleFacts,
)
from domain.tenant.entities import utc_now

KIND_GVW_THRESHOLD = "gvw_threshold"
KIND_ALIAS_MAP = "alias_map"
KIND_NUMERIC_DIFFERENCE = "numeric_difference"


class RuleEngine:
    """Deterministic, version-aware enrichment. Rules are data; this class only interprets them."""

    def evaluate(
        self,
        rules: Sequence[Rule],
        facts: VehicleFacts,
        *,
        at: datetime | None = None,
    ) -> list[RuleResult]:
        moment = at or utc_now()
        selected = self._select_effective_rules(rules, moment)
        derived: dict[str, str] = dict(facts.known_attributes)
        results: list[RuleResult] = []
        for rule in selected:
            result = self._apply(rule, facts, derived, moment)
            results.append(result)
            if result.applied and result.value is not None:
                derived[result.attribute] = result.value
        return results

    def _select_effective_rules(self, rules: Sequence[Rule], moment: datetime) -> list[Rule]:
        effective = [rule for rule in rules if rule.is_effective_at(moment)]
        chosen: dict[str, Rule] = {}
        for rule in effective:
            current = chosen.get(rule.rule_id)
            if current is None or _version_key(rule) > _version_key(current):
                chosen[rule.rule_id] = rule
        return sorted(chosen.values(), key=lambda rule: (rule.priority, rule.rule_id))

    def _apply(
        self,
        rule: Rule,
        facts: VehicleFacts,
        derived: dict[str, str],
        moment: datetime,
    ) -> RuleResult:
        expression = rule.expression
        kind = str(expression.get("kind", rule.rule_type))
        attribute = str(expression["attribute"])
        derive_if_present = bool(expression.get("derive_if_present", False))
        if attribute in derived and not derive_if_present:
            return _skipped(rule, attribute, "attribute already present")

        if kind == KIND_GVW_THRESHOLD:
            return self._apply_threshold(rule, facts, attribute, expression, moment)
        if kind == KIND_ALIAS_MAP:
            return self._apply_alias(rule, facts, attribute, expression, moment)
        if kind == KIND_NUMERIC_DIFFERENCE:
            return self._apply_difference(rule, facts, attribute, expression, moment)
        raise ValueError(f"unsupported rule expression kind: {kind}")

    def _apply_threshold(
        self,
        rule: Rule,
        facts: VehicleFacts,
        attribute: str,
        expression: dict[str, Any],
        moment: datetime,
    ) -> RuleResult:
        input_field = str(expression.get("input", "gvw_kg"))
        value = facts.numeric(input_field)
        if value is None:
            return _skipped(rule, attribute, f"{input_field} is missing")
        code = select_threshold_code(value, list(expression["bands"]))
        if code is None:
            return _skipped(rule, attribute, "no matching threshold band")
        return _applied(
            rule,
            attribute=attribute,
            value=code,
            source_field=input_field,
            transformation_type=KIND_GVW_THRESHOLD,
            confidence=1.0,
            moment=moment,
        )

    def _apply_alias(
        self,
        rule: Rule,
        facts: VehicleFacts,
        attribute: str,
        expression: dict[str, Any],
        moment: datetime,
    ) -> RuleResult:
        input_field = str(expression["input"])
        raw = facts.text(input_field)
        if raw is None or not raw.strip():
            return _skipped(rule, attribute, f"{input_field} is missing")
        aliases = {
            str(code): [str(alias) for alias in values]
            for code, values in expression["aliases"].items()
        }
        matched = match_alias(raw, aliases)
        if matched is None:
            return _skipped(rule, attribute, "no alias matched")
        code, confidence = matched
        return _applied(
            rule,
            attribute=attribute,
            value=code,
            source_field=input_field,
            transformation_type=KIND_ALIAS_MAP,
            confidence=confidence,
            moment=moment,
        )

    def _apply_difference(
        self,
        rule: Rule,
        facts: VehicleFacts,
        attribute: str,
        expression: dict[str, Any],
        moment: datetime,
    ) -> RuleResult:
        minuend_field = str(expression.get("minuend", "gvw_kg"))
        subtrahend_field = str(expression.get("subtrahend", "unladen_weight_kg"))
        minuend = facts.numeric(minuend_field)
        subtrahend = facts.numeric(subtrahend_field)
        if minuend is None or subtrahend is None:
            return _skipped(rule, attribute, "gvw_kg or unladen_weight_kg is missing")
        payload = minuend - subtrahend
        if payload < 0:
            return _skipped(rule, attribute, "unladen weight exceeds GVW")
        return _applied(
            rule,
            attribute=attribute,
            value=str(payload),
            source_field=f"{minuend_field}-{subtrahend_field}",
            transformation_type=KIND_NUMERIC_DIFFERENCE,
            confidence=1.0,
            moment=moment,
        )


def _version_key(rule: Rule) -> tuple[datetime, str]:
    return (rule.effective_from or datetime.min.replace(tzinfo=UTC), rule.version)


def _skipped(rule: Rule, attribute: str, reason: str) -> RuleResult:
    return RuleResult(
        rule_id=rule.rule_id,
        rule_version=rule.version,
        attribute=attribute,
        value=None,
        applied=False,
        skipped_reason=reason,
        provenance=None,
    )


def _applied(
    rule: Rule,
    *,
    attribute: str,
    value: str,
    source_field: str,
    transformation_type: str,
    confidence: float,
    moment: datetime,
) -> RuleResult:
    return RuleResult(
        rule_id=rule.rule_id,
        rule_version=rule.version,
        attribute=attribute,
        value=value,
        applied=True,
        skipped_reason=None,
        provenance=AttributeProvenance(
            attribute=attribute,
            value=value,
            source=SOURCE_DERIVED,
            source_system=SOURCE_SYSTEM_RULE_ENGINE,
            source_field=source_field,
            source_record_id=None,
            transformation_type=transformation_type,
            rule_id=rule.rule_id,
            rule_version=rule.version,
            confidence=confidence,
            timestamp=moment,
        ),
    )
