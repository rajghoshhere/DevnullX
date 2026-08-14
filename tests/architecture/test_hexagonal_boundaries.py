from pathlib import Path

FORBIDDEN_SNIPPETS = (
    "api_setu",
    "apisetu",
    "ElementTree",
    "xml.etree",
    "rc_regn_no",
    "rc_maker_desc",
    "rc_gvw",
    "X-APISETU",
)


def test_domain_and_application_do_not_know_api_setu_xml() -> None:
    roots = [Path("src/domain"), Path("src/application")]
    violations: list[str] = []
    for root in roots:
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for snippet in FORBIDDEN_SNIPPETS:
                if snippet in text:
                    violations.append(f"{path}: {snippet}")
    assert violations == []
