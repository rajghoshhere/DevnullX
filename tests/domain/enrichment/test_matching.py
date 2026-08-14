from domain.enrichment.matching import match_alias, normalize_label, select_threshold_code


def test_normalize_label_strips_punctuation_and_case() -> None:
    assert normalize_label("TRUCK (OPEN BODY)") == "TRUCK OPEN BODY"
    assert normalize_label("  tata-motors  ltd ") == "TATA MOTORS LTD"


def test_longest_exact_alias_wins() -> None:
    matched = match_alias(
        "OPEN BODY",
        {"OPEN": ["OPEN"], "HIGH_SIDE": ["OPEN BODY"]},
    )
    assert matched == ("HIGH_SIDE", 1.0)


def test_threshold_uses_first_matching_inclusive_band() -> None:
    bands = [
        {"max_inclusive": 3500, "code": "N1"},
        {"max_inclusive": 12000, "code": "N2"},
        {"max_inclusive": None, "code": "N3"},
    ]
    assert select_threshold_code(3500, bands) == "N1"
    assert select_threshold_code(3501, bands) == "N2"
    assert select_threshold_code(12000, bands) == "N2"
    assert select_threshold_code(12001, bands) == "N3"
