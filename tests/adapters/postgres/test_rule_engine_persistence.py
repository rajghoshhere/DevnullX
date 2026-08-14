from adapters.postgres.rule_repository import PostgresProvenanceRepository, PostgresRuleRepository
from adapters.postgres.rule_seed import builtin_rules, seed_rules
from domain.enrichment.engine import RuleEngine
from domain.enrichment.models import SOURCE_DERIVED, VehicleAttributeProvenance, VehicleFacts
from tests.adapters.postgres.helpers import seed_graph
from tests.domain.enrichment.rules import FIXED_AT


async def test_seeded_rules_round_trip_and_provenance_persistence(db_session) -> None:
    await seed_rules(db_session)
    rules = list(await PostgresRuleRepository(db_session).list_effective(at=FIXED_AT))
    assert {rule.rule_id for rule in rules} >= {
        "RULE-GVW-N-CATEGORY-001",
        "RULE-GVW-SEGMENT-001",
        "RULE-BODY-TYPE-ALIAS-001",
        "RULE-MANUFACTURER-ALIAS-001",
        "RULE-ESTIMATED-PAYLOAD-001",
    }

    tenant, _owner, _fleet, _manufacturer, _truck_model, vehicle = await seed_graph(db_session)
    results = RuleEngine().evaluate(
        builtin_rules(),
        VehicleFacts(gvw_kg=vehicle.gvw_kg, unladen_weight_kg=vehicle.unladen_weight_kg),
        at=FIXED_AT,
    )
    applied = [item for item in results if item.applied]
    assert {item.attribute: item.value for item in applied}["regulatory_category"] == "N3"

    repo = PostgresProvenanceRepository(db_session)
    for item in applied:
        await repo.add(
            VehicleAttributeProvenance.from_result(
                tenant_id=tenant.id,
                vehicle_id=vehicle.id,
                result=item,
            )
        )
    stored = await repo.list_for_vehicle(vehicle.id)
    assert stored
    assert all(row.source == SOURCE_DERIVED for row in stored)
    assert all(row.rule_id and row.rule_version for row in stored)
    assert all(row.confidence == 1.0 for row in stored)
