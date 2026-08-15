from uuid import uuid4

import pytest
from tests.application.fakes import (
    InMemoryFleetOwnerRepository,
    InMemoryFleetRepository,
    InMemoryTenantRepository,
    InMemoryVehicleRepository,
    seed_tenant_and_fleet,
)

from adapters.vehicle_providers.fake import FakeVehicleVerificationProvider
from application.commands.create_fleet import CreateFleet
from application.commands.create_fleet_owner import CreateFleetOwner
from application.commands.create_tenant import CreateTenant
from application.commands.create_vehicle import CreateVehicle
from application.commands.submit_vehicle_for_verification import SubmitVehicleForVerification
from application.commands.verify_vehicles_batch import VerifyVehiclesBatch
from application.errors import ConflictError, InvalidStateError, NotFoundError
from domain.tenant.entities import Tenant
from domain.vehicle.states import VehicleStatus


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
    fleet = await CreateFleet(tenants, fleets).execute(
        tenant_id=tenant.id, name="North Fleet"
    )
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
    await use_case.execute(
        tenant_id=tenant.id, fleet_id=fleet.id, registration_number="MH12AB1234"
    )
    with pytest.raises(ConflictError, match="registration"):
        await use_case.execute(
            tenant_id=tenant.id, fleet_id=fleet.id, registration_number="mh-12-ab-1234"
        )


async def test_submit_vehicle_success_reaches_verified() -> None:
    tenant, fleet, tenants, fleets = await seed_tenant_and_fleet()
    vehicles = InMemoryVehicleRepository()
    created = await CreateVehicle(tenants, fleets, vehicles).execute(
        tenant_id=tenant.id,
        fleet_id=fleet.id,
        registration_number="MH12AB1234",
    )
    provider = FakeVehicleVerificationProvider()
    verified = await SubmitVehicleForVerification(vehicles, provider).execute(
        tenant_id=tenant.id,
        vehicle_id=created.id,
    )
    assert verified.vehicle_status is VehicleStatus.VERIFIED
    assert provider.calls[0][0] == "MH12AB1234"
    assert verified.gvw_kg == 47500
    assert verified.unladen_weight_kg == 12500
    assert verified.engine_cc == 6700
    assert verified.cylinder_count == 6
    assert verified.fuel_type == "DIESEL"
    assert verified.body_type == "OPEN"


async def test_submit_vehicle_failure_goes_to_manual_review() -> None:
    tenant, fleet, tenants, fleets = await seed_tenant_and_fleet()
    vehicles = InMemoryVehicleRepository()
    created = await CreateVehicle(tenants, fleets, vehicles).execute(
        tenant_id=tenant.id,
        fleet_id=fleet.id,
        registration_number="MH12FAIL99",
    )
    result = await SubmitVehicleForVerification(
        vehicles, FakeVehicleVerificationProvider()
    ).execute(tenant_id=tenant.id, vehicle_id=created.id)
    assert result.vehicle_status is VehicleStatus.MANUAL_REVIEW


async def test_submit_vehicle_can_capture_registration() -> None:
    tenant, fleet, tenants, fleets = await seed_tenant_and_fleet()
    vehicles = InMemoryVehicleRepository()
    created = await CreateVehicle(tenants, fleets, vehicles).execute(
        tenant_id=tenant.id,
        fleet_id=fleet.id,
    )
    result = await SubmitVehicleForVerification(
        vehicles, FakeVehicleVerificationProvider()
    ).execute(
        tenant_id=tenant.id,
        vehicle_id=created.id,
        registration_number="KA01CD5678",
    )
    assert result.registration_number == "KA01CD5678"
    assert result.vehicle_status is VehicleStatus.VERIFIED


async def test_submit_without_registration_is_invalid() -> None:
    tenant, fleet, tenants, fleets = await seed_tenant_and_fleet()
    vehicles = InMemoryVehicleRepository()
    created = await CreateVehicle(tenants, fleets, vehicles).execute(
        tenant_id=tenant.id,
        fleet_id=fleet.id,
    )
    with pytest.raises(InvalidStateError, match="registration"):
        await SubmitVehicleForVerification(
            vehicles, FakeVehicleVerificationProvider()
        ).execute(tenant_id=tenant.id, vehicle_id=created.id)


async def test_submit_from_verified_is_invalid() -> None:
    tenant, fleet, tenants, fleets = await seed_tenant_and_fleet()
    vehicles = InMemoryVehicleRepository()
    created = await CreateVehicle(tenants, fleets, vehicles).execute(
        tenant_id=tenant.id,
        fleet_id=fleet.id,
        registration_number="MH12AB1234",
    )
    use_case = SubmitVehicleForVerification(vehicles, FakeVehicleVerificationProvider())
    await use_case.execute(tenant_id=tenant.id, vehicle_id=created.id)
    with pytest.raises(InvalidStateError):
        await use_case.execute(tenant_id=tenant.id, vehicle_id=created.id)


async def test_submit_missing_vehicle() -> None:
    use_case = SubmitVehicleForVerification(
        InMemoryVehicleRepository(), FakeVehicleVerificationProvider()
    )
    with pytest.raises(NotFoundError, match="vehicle"):
        await use_case.execute(tenant_id=uuid4(), vehicle_id=uuid4())


async def test_batch_verify_populates_and_isolates_failures() -> None:
    tenant, fleet, tenants, fleets = await seed_tenant_and_fleet()
    vehicles = InMemoryVehicleRepository()
    create = CreateVehicle(tenants, fleets, vehicles)
    first = await create.execute(
        tenant_id=tenant.id, fleet_id=fleet.id, registration_number="MH12AB1234"
    )
    second = await create.execute(
        tenant_id=tenant.id, fleet_id=fleet.id, registration_number="KA01FAIL99"
    )
    result = await VerifyVehiclesBatch(
        SubmitVehicleForVerification(vehicles, FakeVehicleVerificationProvider())
    ).execute(tenant_id=tenant.id, vehicle_ids=[first.id, second.id, uuid4()])
    assert result.requested == 3
    assert result.verified == 1
    assert result.failed == 2
    by_id = {item.vehicle_id: item for item in result.items}
    assert by_id[first.id].ok is True
    assert by_id[first.id].vehicle is not None
    assert by_id[first.id].vehicle.gvw_kg == 47500
    assert by_id[second.id].ok is False
    assert by_id[second.id].vehicle is not None
    assert by_id[second.id].vehicle.vehicle_status is VehicleStatus.MANUAL_REVIEW

