import pytest
from tests.domain.enrichment.rules import (
    FIXED_AT,
    all_requirement_rules,
    body_type_rule,
    gvw_category_rule,
    manufacturer_rule,
    payload_rule,
    segment_rule,
)

from domain.enrichment.engine import RuleEngine
from domain.enrichment.models import SOURCE_DERIVED, SOURCE_SYSTEM_RULE_ENGINE, VehicleFacts

engine = RuleEngine()


def _applied(results, attribute: str):
    matches = [result for result in results if result.attribute == attribute and result.applied]
    assert matches, f"expected applied result for {attribute}: {results}"
    return matches[0]


@pytest.mark.parametrize(
    ("gvw_kg", "code"),
    [
        (0, "N1"),
        (3500, "N1"),
        (3501, "N2"),
        (12000, "N2"),
        (12001, "N3"),
        (47500, "N3"),
    ],
)
def test_regulatory_category_from_gvw(gvw_kg: int, code: str) -> None:
    results = engine.evaluate([gvw_category_rule()], VehicleFacts(gvw_kg=gvw_kg), at=FIXED_AT)
    result = _applied(results, "regulatory_category")
    assert result.value == code
    assert result.rule_id == "RULE-GVW-N-CATEGORY-001"
    assert result.rule_version == "1.0.0"
    assert result.provenance is not None
    assert result.provenance.source == SOURCE_DERIVED
    assert result.provenance.source_system == SOURCE_SYSTEM_RULE_ENGINE
    assert result.provenance.source_field == "gvw_kg"
    assert result.provenance.rule_id == "RULE-GVW-N-CATEGORY-001"
    assert result.provenance.rule_version == "1.0.0"
    assert result.provenance.confidence == 1.0
    assert result.provenance.transformation_type == "gvw_threshold"
    assert result.provenance.timestamp == FIXED_AT


@pytest.mark.parametrize(
    ("gvw_kg", "code"),
    [
        (3500, "LCV"),
        (7500, "LCV"),
        (7501, "ICV"),
        (16200, "ICV"),
        (16201, "MHCV"),
        (25000, "MHCV"),
        (25001, "HCV"),
    ],
)
def test_commercial_segment_from_gvw(gvw_kg: int, code: str) -> None:
    result = _applied(
        engine.evaluate([segment_rule()], VehicleFacts(gvw_kg=gvw_kg), at=FIXED_AT),
        "truck_segment",
    )
    assert result.value == code


@pytest.mark.parametrize(
    ("raw", "code", "confidence"),
    [
        ("TRUCK (OPEN BODY)", "OPEN", 1.0),
        ("truck open body", "OPEN", 1.0),
        ("TIPPER", "TIPPER", 1.0),
        ("DUMPER", "TIPPER", 1.0),
        ("Tata 1613 Dumper 6x4", "TIPPER", 0.9),
    ],
)
def test_body_type_normalization(raw: str, code: str, confidence: float) -> None:
    result = _applied(
        engine.evaluate([body_type_rule()], VehicleFacts(raw_body_text=raw), at=FIXED_AT),
        "body_type",
    )
    assert result.value == code
    assert result.provenance is not None
    assert result.provenance.confidence == confidence
    assert result.provenance.source == SOURCE_DERIVED


def test_manufacturer_normalization() -> None:
    result = _applied(
        engine.evaluate(
            [manufacturer_rule()],
            VehicleFacts(raw_manufacturer="TATA MOTORS LTD"),
            at=FIXED_AT,
        ),
        "manufacturer",
    )
    assert result.value == "TATA_MOTORS"
    assert result.provenance is not None
    assert result.provenance.confidence == 1.0


def test_estimated_payload_is_gvw_minus_unladen_and_flagged_derived() -> None:
    result = _applied(
        engine.evaluate(
            [payload_rule()],
            VehicleFacts(gvw_kg=47500, unladen_weight_kg=12500),
            at=FIXED_AT,
        ),
        "estimated_payload_kg",
    )
    assert result.value == "35000"
    assert result.provenance is not None
    assert result.provenance.source == SOURCE_DERIVED
    assert result.provenance.transformation_type == "numeric_difference"
    assert result.provenance.confidence == 1.0


def test_estimated_payload_recomputes_even_when_already_present() -> None:
    result = _applied(
        engine.evaluate(
            [payload_rule()],
            VehicleFacts(
                gvw_kg=10000,
                unladen_weight_kg=4000,
                known_attributes={"estimated_payload_kg": "1"},
            ),
            at=FIXED_AT,
        ),
        "estimated_payload_kg",
    )
    assert result.value == "6000"


def test_skips_when_gvw_missing() -> None:
    results = engine.evaluate([gvw_category_rule()], VehicleFacts(), at=FIXED_AT)
    assert results[0].applied is False
    assert results[0].skipped_reason == "gvw_kg is missing"
    assert results[0].provenance is None


def test_skips_when_payload_inputs_missing() -> None:
    results = engine.evaluate([payload_rule()], VehicleFacts(gvw_kg=12000), at=FIXED_AT)
    assert results[0].applied is False
    assert "missing" in (results[0].skipped_reason or "")


def test_skips_when_unladen_exceeds_gvw() -> None:
    results = engine.evaluate(
        [payload_rule()],
        VehicleFacts(gvw_kg=8000, unladen_weight_kg=9000),
        at=FIXED_AT,
    )
    assert results[0].applied is False
    assert results[0].skipped_reason == "unladen weight exceeds GVW"


def test_does_not_override_known_regulatory_category() -> None:
    results = engine.evaluate(
        [gvw_category_rule()],
        VehicleFacts(gvw_kg=20000, known_attributes={"regulatory_category": "N2"}),
        at=FIXED_AT,
    )
    assert results[0].applied is False
    assert results[0].skipped_reason == "attribute already present"


def test_inactive_rules_are_ignored() -> None:
    results = engine.evaluate(
        [gvw_category_rule(active=False)],
        VehicleFacts(gvw_kg=20000),
        at=FIXED_AT,
    )
    assert results == []


def test_expired_rules_are_ignored() -> None:
    from datetime import timedelta

    expired = gvw_category_rule(effective_to=FIXED_AT)
    results = engine.evaluate([expired], VehicleFacts(gvw_kg=20000), at=FIXED_AT)
    assert results == []
    still_valid = gvw_category_rule(effective_to=FIXED_AT + timedelta(seconds=1))
    assert (
        _applied(
            engine.evaluate([still_valid], VehicleFacts(gvw_kg=20000), at=FIXED_AT),
            "regulatory_category",
        ).value
        == "N3"
    )


def test_not_yet_effective_rules_are_ignored() -> None:
    from datetime import timedelta

    future = gvw_category_rule(effective_from=FIXED_AT + timedelta(days=1))
    assert engine.evaluate([future], VehicleFacts(gvw_kg=20000), at=FIXED_AT) == []


def test_newer_version_of_same_rule_id_wins() -> None:
    v1 = gvw_category_rule(version="1.0.0")
    v2 = gvw_category_rule(
        version="2.0.0",
        expression={
            "kind": "gvw_threshold",
            "attribute": "regulatory_category",
            "input": "gvw_kg",
            "bands": [{"max_inclusive": None, "code": "N3"}],
        },
    )
    result = _applied(
        engine.evaluate([v1, v2], VehicleFacts(gvw_kg=2000), at=FIXED_AT),
        "regulatory_category",
    )
    assert result.value == "N3"
    assert result.rule_version == "2.0.0"


def test_priority_orders_rules_and_first_writer_wins() -> None:
    low = gvw_category_rule(priority=10)
    high_number = gvw_category_rule(
        rule_id="RULE-GVW-N-CATEGORY-OVERRIDE",
        priority=99,
        expression={
            "kind": "gvw_threshold",
            "attribute": "regulatory_category",
            "input": "gvw_kg",
            "bands": [{"max_inclusive": None, "code": "N3"}],
        },
    )
    results = engine.evaluate([high_number, low], VehicleFacts(gvw_kg=2000), at=FIXED_AT)
    result = _applied(results, "regulatory_category")
    assert result.value == "N1"
    skipped = [item for item in results if not item.applied]
    assert skipped[0].rule_id == "RULE-GVW-N-CATEGORY-OVERRIDE"


def test_unknown_expression_kind_raises() -> None:
    rule = gvw_category_rule(
        expression={"kind": "llm", "attribute": "regulatory_category"},
    )
    with pytest.raises(ValueError, match="unsupported rule expression kind"):
        engine.evaluate([rule], VehicleFacts(gvw_kg=1000), at=FIXED_AT)


def test_no_alias_match_is_skipped() -> None:
    results = engine.evaluate(
        [body_type_rule()],
        VehicleFacts(raw_body_text="UNKNOWN BODY STYLE"),
        at=FIXED_AT,
    )
    assert results[0].applied is False
    assert results[0].skipped_reason == "no alias matched"


def test_full_requirement_set_is_deterministic() -> None:
    facts = VehicleFacts(
        gvw_kg=47500,
        unladen_weight_kg=12500,
        raw_body_text="TRUCK (OPEN BODY)",
        raw_manufacturer="TATA MOTORS LTD",
    )
    first = engine.evaluate(all_requirement_rules(), facts, at=FIXED_AT)
    second = engine.evaluate(all_requirement_rules(), facts, at=FIXED_AT)
    applied = {item.attribute: item.value for item in first if item.applied}
    assert applied == {
        "regulatory_category": "N3",
        "truck_segment": "HCV",
        "body_type": "OPEN",
        "manufacturer": "TATA_MOTORS",
        "estimated_payload_kg": "35000",
    }
    assert [item.provenance for item in first] == [item.provenance for item in second]
    for item in first:
        if item.applied:
            assert item.provenance is not None
            assert item.provenance.rule_id == item.rule_id
            assert item.provenance.rule_version == item.rule_version
            assert item.provenance.source == SOURCE_DERIVED
            assert item.provenance.confidence >= 0.9
