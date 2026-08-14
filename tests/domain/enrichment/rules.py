from datetime import UTC, datetime
from typing import Any

from domain.enrichment.models import Rule

FIXED_AT = datetime(2026, 1, 15, tzinfo=UTC)


def gvw_category_rule(**overrides: Any) -> Rule:
    return _make_rule(
        {
            "rule_id": "RULE-GVW-N-CATEGORY-001",
            "name": "Regulatory category from GVW",
            "version": "1.0.0",
            "rule_type": "gvw_threshold",
            "priority": 10,
            "expression": {
                "kind": "gvw_threshold",
                "attribute": "regulatory_category",
                "input": "gvw_kg",
                "bands": [
                    {"max_inclusive": 3500, "code": "N1"},
                    {"max_inclusive": 12000, "code": "N2"},
                    {"max_inclusive": None, "code": "N3"},
                ],
            },
            "effective_from": datetime(2020, 1, 1, tzinfo=UTC),
        },
        overrides,
    )


def segment_rule(**overrides: Any) -> Rule:
    return _make_rule(
        {
            "rule_id": "RULE-GVW-SEGMENT-001",
            "name": "Commercial segment from GVW",
            "version": "1.0.0",
            "rule_type": "gvw_threshold",
            "priority": 20,
            "expression": {
                "kind": "gvw_threshold",
                "attribute": "truck_segment",
                "input": "gvw_kg",
                "bands": [
                    {"max_inclusive": 7500, "code": "LCV"},
                    {"max_inclusive": 16200, "code": "ICV"},
                    {"max_inclusive": 25000, "code": "MHCV"},
                    {"max_inclusive": None, "code": "HCV"},
                ],
            },
            "effective_from": datetime(2020, 1, 1, tzinfo=UTC),
        },
        overrides,
    )


def body_type_rule(**overrides: Any) -> Rule:
    return _make_rule(
        {
            "rule_id": "RULE-BODY-TYPE-ALIAS-001",
            "name": "Body type normalization",
            "version": "1.0.0",
            "rule_type": "alias_map",
            "priority": 30,
            "expression": {
                "kind": "alias_map",
                "attribute": "body_type",
                "input": "raw_body_text",
                "aliases": {
                    "OPEN": ["TRUCK (OPEN BODY)", "OPEN BODY", "OPEN"],
                    "TIPPER": ["TIPPER", "DUMPER"],
                    "TANKER": ["TANKER", "TANK"],
                },
            },
            "effective_from": datetime(2020, 1, 1, tzinfo=UTC),
        },
        overrides,
    )


def manufacturer_rule(**overrides: Any) -> Rule:
    return _make_rule(
        {
            "rule_id": "RULE-MANUFACTURER-ALIAS-001",
            "name": "Manufacturer normalization",
            "version": "1.0.0",
            "rule_type": "alias_map",
            "priority": 40,
            "expression": {
                "kind": "alias_map",
                "attribute": "manufacturer",
                "input": "raw_manufacturer",
                "aliases": {
                    "TATA_MOTORS": ["TATA MOTORS LTD", "TATA MOTORS", "TATA"],
                },
            },
            "effective_from": datetime(2020, 1, 1, tzinfo=UTC),
        },
        overrides,
    )


def payload_rule(**overrides: Any) -> Rule:
    return _make_rule(
        {
            "rule_id": "RULE-ESTIMATED-PAYLOAD-001",
            "name": "Estimated payload",
            "version": "1.0.0",
            "rule_type": "numeric_difference",
            "priority": 50,
            "expression": {
                "kind": "numeric_difference",
                "attribute": "estimated_payload_kg",
                "minuend": "gvw_kg",
                "subtrahend": "unladen_weight_kg",
                "derive_if_present": True,
            },
            "effective_from": datetime(2020, 1, 1, tzinfo=UTC),
        },
        overrides,
    )


def all_requirement_rules() -> list[Rule]:
    return [
        gvw_category_rule(),
        segment_rule(),
        body_type_rule(),
        manufacturer_rule(),
        payload_rule(),
    ]


def _make_rule(values: dict[str, Any], overrides: dict[str, Any]) -> Rule:
    merged = {**values, **overrides}
    return Rule.create(
        rule_id=str(merged["rule_id"]),
        name=str(merged["name"]),
        version=str(merged["version"]),
        rule_type=str(merged["rule_type"]),
        expression=merged["expression"],
        priority=int(merged["priority"]),
        active=bool(merged.get("active", True)),
        effective_from=merged.get("effective_from"),
        effective_to=merged.get("effective_to"),
        author=merged.get("author"),
    )
