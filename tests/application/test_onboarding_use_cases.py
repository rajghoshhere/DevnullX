from collections.abc import Sequence
from uuid import uuid4

import pytest
from tests.application.fakes import (
    InMemoryFleetOwnerRepository,
    InMemoryFleetRepository,
    InMemoryProvenanceRepository,
    InMemoryRuleRepository,
    InMemoryTenantRepository,
    InMemoryVehicleRepository,
    seed_tenant_and_fleet,
)
from tests.domain.enrichment.rules import payload_rule

from adapters.vehicle_providers.fake import FakeVehicleVerificationProvider
from application.commands.create_fleet import CreateFleet
from application.commands.create_fleet_owner import CreateFleetOwner
from application.commands.create_tenant import CreateTenant
from application.commands.create_vehicle import CreateVehicle
from application.commands.populate_vehicle import PopulateVehicle
from application.commands.populate_vehicles_batch import PopulateVehiclesBatch
from application.commands.review_vehicle import ReviewVehicle
from application.errors import ConflictError, InvalidStateError, NotFoundError
from domain.enrichment.models import Rule
from domain.tenant.entities import Tenant
from domain.vehicle.entities import Vehicle
from domain.vehicle.states import VehicleStatus
from ports.vehicle_provider import VehicleVerificationProvider


def _populate(
    vehicles: InMemoryVehicleRepository,
    provider: VehicleVerificationProvider | None = None,
    rules: Sequence[Rule] | None = None,
    provenance: InMemoryProvenanceRepository | None = None,
) -> PopulateVehicle:
    return PopulateVehicle(
        vehicles,
        provider or FakeVehicleVerificationProvider(),
        InMemoryRuleRepository(rules),
        provenance or InMemoryProvenanceRepository(),
    )


async def test_create_tenant() -> None:
    tenants = InMemoryTenantRepository()
    tenant = await CreateTenant(tenants).execute(name=" Acme ")
    assert tenant.name == "Acme"
    assert await tenants.get_by_id(tenant.id) is tenant


async def test_create_fleet_owner_requires_tenant() -> None:
    use_case = CreateFleetOwner(InMemoryTenantRepository(), InMemoryFleetOwnerRepository())
    with pytest.raises(NotFoundError, match="tenant"):
        await use_case.execute(tenant_id=uuid4(), name="Owner")


async def test_create_fleet_owner() -> None:
    tenants = InMemoryTenantRepository()
    owners = InMemoryFleetOwnerRepository()
    tenant = await tenants.add(Tenant.create("Acme"))
    owner = await CreateFleetOwner(tenants, owners).execute(tenant_id=tenant.id, name="Ravi")
    assert owner.tenant_id == tenant.id
    assert owner.name == "Ravi"


async def test_create_fleet_requires_tenant() -> None:
    use_case = CreateFleet(InMemoryTenantRepository(), InMemoryFleetRepository())
    with pytest.raises(NotFoundError, match="tenant"):
        await use_case.execute(tenant_id=uuid4(), name="Fleet")


async def test_create_fleet() -> None:
    tenants = InMemoryTenantRepository()
    fleets = InMemoryFleetRepository()
    tenant = await tenants.add(Tenant.create("Acme Logistics"))
    fleet = await CreateFleet(tenants, fleets).execute(tenant_id=tenant.id, name="North Fleet")
    assert fleet.tenant_id == tenant.id
    assert fleet.name == "North Fleet"


async def test_create_vehicle_starts_in_draft() -> None:
    tenant, fleet, tenants, fleets = await seed_tenant_and_fleet()
    vehicles = InMemoryVehicleRepository()
    vehicle = await CreateVehicle(tenants, fleets, vehicles).execute(
        tenant_id=tenant.id,
        fleet_id=fleet.id,
        registration_number="MH-12-AB-1234",
    )
    assert vehicle.vehicle_status is VehicleStatus.DRAFT
    assert vehicle.normalized_registration_number == "MH12AB1234"


async def test_create_vehicle_missing_fleet() -> None:
    tenant, _fleet, tenants, fleets = await seed_tenant_and_fleet()
    use_case = CreateVehicle(tenants, fleets, InMemoryVehicleRepository())
    with pytest.raises(NotFoundError, match="fleet"):
        await use_case.execute(tenant_id=tenant.id, fleet_id=uuid4())


async def test_create_vehicle_rejects_foreign_fleet() -> None:
    tenant, _fleet, tenants, fleets = await seed_tenant_and_fleet()
    other_tenant, other_fleet, _, _ = await seed_tenant_and_fleet(
        tenants, fleets, tenant_name="Other", fleet_name="Other Fleet"
    )
    use_case = CreateVehicle(tenants, fleets, InMemoryVehicleRepository())
    with pytest.raises(NotFoundError, match="fleet"):
        await use_case.execute(tenant_id=tenant.id, fleet_id=other_fleet.id)
    assert other_tenant.id != tenant.id


async def test_create_vehicle_rejects_duplicate_registration() -> None:
    tenant, fleet, tenants, fleets = await seed_tenant_and_fleet()
    vehicles = InMemoryVehicleRepository()
    use_case = CreateVehicle(tenants, fleets, vehicles)
    await use_case.execute(tenant_id=tenant.id, fleet_id=fleet.id, registration_number="MH12AB1234")
    with pytest.raises(ConflictError, match="registration"):
        await use_case.execute(
            tenant_id=tenant.id, fleet_id=fleet.id, registration_number="mh-12-ab-1234"
        )


async def _draft_vehicle(
    *,
    registration_number: str | None = "MH12AB1234",
) -> tuple[Tenant, Vehicle, InMemoryVehicleRepository]:
    tenant, fleet, tenants, fleets = await seed_tenant_and_fleet()
    vehicles = InMemoryVehicleRepository()
    created = await CreateVehicle(tenants, fleets, vehicles).execute(
        tenant_id=tenant.id,
        fleet_id=fleet.id,
        registration_number=registration_number,
    )
    return tenant, created, vehicles


async def test_populate_success_reaches_ready_for_review() -> None:
    tenant, created, vehicles = await _draft_vehicle()
    provider = FakeVehicleVerificationProvider()
    populated = await _populate(vehicles, provider).execute(
        tenant_id=tenant.id,
        vehicle_id=created.id,
    )
    assert populated.vehicle_status is VehicleStatus.READY_FOR_REVIEW
    assert provider.calls[0][0] == "MH12AB1234"
    assert populated.gvw_kg == 47500
    assert populated.unladen_weight_kg == 12500
    assert populated.engine_cc == 6700
    assert populated.cylinder_count == 6
    assert populated.fuel_type == "DIESEL"
    assert populated.body_type == "OPEN"


async def test_populate_applies_rules_and_stores_provenance() -> None:
    tenant, created, vehicles = await _draft_vehicle()
    provenance = InMemoryProvenanceRepository()
    populated = await _populate(vehicles, rules=[payload_rule()], provenance=provenance).execute(
        tenant_id=tenant.id, vehicle_id=created.id
    )
    assert populated.vehicle_status is VehicleStatus.READY_FOR_REVIEW
    rows = await provenance.list_for_vehicle(created.id)
    assert any(row.attribute == "estimated_payload_kg" and row.value == "35000" for row in rows)


async def test_populate_failure_goes_to_manual_review() -> None:
    tenant, created, vehicles = await _draft_vehicle(registration_number="MH12FAIL99")
    result = await _populate(vehicles).execute(tenant_id=tenant.id, vehicle_id=created.id)
    assert result.vehicle_status is VehicleStatus.MANUAL_REVIEW


async def test_populate_can_retry_from_manual_review() -> None:
    tenant, created, vehicles = await _draft_vehicle(registration_number="MH12FAIL99")
    failed = await _populate(vehicles).execute(tenant_id=tenant.id, vehicle_id=created.id)
    assert failed.vehicle_status is VehicleStatus.MANUAL_REVIEW
    retried = await _populate(vehicles).execute(
        tenant_id=tenant.id,
        vehicle_id=created.id,
        registration_number="MH12AB1234",
    )
    assert retried.vehicle_status is VehicleStatus.READY_FOR_REVIEW


async def test_populate_can_capture_registration() -> None:
    tenant, created, vehicles = await _draft_vehicle(registration_number=None)
    result = await _populate(vehicles).execute(
        tenant_id=tenant.id,
        vehicle_id=created.id,
        registration_number="KA01CD5678",
    )
    assert result.registration_number == "KA01CD5678"
    assert result.vehicle_status is VehicleStatus.READY_FOR_REVIEW


async def test_populate_without_registration_is_invalid() -> None:
    tenant, created, vehicles = await _draft_vehicle(registration_number=None)
    with pytest.raises(InvalidStateError, match="registration"):
        await _populate(vehicles).execute(tenant_id=tenant.id, vehicle_id=created.id)


async def test_populate_from_ready_for_review_is_invalid() -> None:
    tenant, created, vehicles = await _draft_vehicle()
    use_case = _populate(vehicles)
    await use_case.execute(tenant_id=tenant.id, vehicle_id=created.id)
    with pytest.raises(InvalidStateError):
        await use_case.execute(tenant_id=tenant.id, vehicle_id=created.id)


async def test_populate_missing_vehicle() -> None:
    use_case = _populate(InMemoryVehicleRepository())
    with pytest.raises(NotFoundError, match="vehicle"):
        await use_case.execute(tenant_id=uuid4(), vehicle_id=uuid4())


async def test_review_approve_and_reject() -> None:
    tenant, created, vehicles = await _draft_vehicle()
    await _populate(vehicles).execute(tenant_id=tenant.id, vehicle_id=created.id)
    approved = await ReviewVehicle(vehicles).execute(
        tenant_id=tenant.id, vehicle_id=created.id, decision="APPROVE"
    )
    assert approved.vehicle_status is VehicleStatus.APPROVED

    tenant, failed, vehicles = await _draft_vehicle(registration_number="MH12FAIL99")
    await _populate(vehicles).execute(tenant_id=tenant.id, vehicle_id=failed.id)
    rejected = await ReviewVehicle(vehicles).execute(
        tenant_id=tenant.id, vehicle_id=failed.id, decision="REJECT"
    )
    assert rejected.vehicle_status is VehicleStatus.REJECTED


async def test_review_from_draft_is_invalid() -> None:
    tenant, created, vehicles = await _draft_vehicle()
    with pytest.raises(InvalidStateError, match="reviewed"):
        await ReviewVehicle(vehicles).execute(
            tenant_id=tenant.id, vehicle_id=created.id, decision="APPROVE"
        )


async def test_batch_populate_isolates_failures() -> None:
    tenant, fleet, tenants, fleets = await seed_tenant_and_fleet()
    vehicles = InMemoryVehicleRepository()
    create = CreateVehicle(tenants, fleets, vehicles)
    first = await create.execute(
        tenant_id=tenant.id, fleet_id=fleet.id, registration_number="MH12AB1234"
    )
    second = await create.execute(
        tenant_id=tenant.id, fleet_id=fleet.id, registration_number="KA01FAIL99"
    )
    result = await PopulateVehiclesBatch(_populate(vehicles)).execute(
        tenant_id=tenant.id, vehicle_ids=[first.id, second.id, uuid4()]
    )
    assert result.requested == 3
    assert result.populated == 1
    assert result.verified == 1
    assert result.failed == 2
    by_id = {item.vehicle_id: item for item in result.items}
    assert by_id[first.id].ok is True
    assert by_id[first.id].vehicle is not None
    assert by_id[first.id].vehicle.gvw_kg == 47500
    assert by_id[second.id].ok is False
    assert by_id[second.id].vehicle is not None
    assert by_id[second.id].vehicle.vehicle_status is VehicleStatus.MANUAL_REVIEW
