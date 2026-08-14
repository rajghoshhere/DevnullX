import pytest
from sqlalchemy.exc import IntegrityError

from adapters.postgres.fleet_repository import PostgresFleetRepository
from adapters.postgres.tenant_repository import PostgresTenantRepository
from adapters.postgres.vehicle_repository import PostgresVehicleRepository
from domain.fleet.entities import Fleet
from domain.tenant.entities import Tenant
from domain.vehicle.entities import Vehicle
from domain.vehicle.registration import normalize_registration_number
from tests.adapters.postgres.helpers import seed_graph


async def test_same_tenant_cannot_reuse_normalized_registration_number(db_session) -> None:
    tenant, _owner, fleet, _manufacturer, truck_model, _vehicle = await seed_graph(
        db_session, registration_number="MH-12-AB-1234"
    )

    duplicate = Vehicle.create(
        tenant_id=tenant.id,
        fleet_id=fleet.id,
        truck_model_id=truck_model.id,
        registration_number="mh12ab1234",
    )
    assert duplicate.normalized_registration_number == "MH12AB1234"

    with pytest.raises(IntegrityError):
        async with db_session.begin_nested():
            await PostgresVehicleRepository(db_session).add(duplicate)
            await db_session.flush()


async def test_different_tenants_can_share_registration_number(db_session) -> None:
    await seed_graph(db_session, registration_number="MH12AB1234")

    other_tenant = Tenant.create("Beta Transport")
    other_fleet = Fleet.create(tenant_id=other_tenant.id, name="East Fleet")
    await PostgresTenantRepository(db_session).add(other_tenant)
    await PostgresFleetRepository(db_session).add(other_fleet)

    other_vehicle = Vehicle.create(
        tenant_id=other_tenant.id,
        fleet_id=other_fleet.id,
        registration_number="MH12AB1234",
    )
    saved = await PostgresVehicleRepository(db_session).add(other_vehicle)
    await db_session.flush()

    found = await PostgresVehicleRepository(db_session).get_by_normalized_registration(
        other_tenant.id,
        "MH12AB1234",
    )
    assert found is not None
    assert found.id == saved.id


def test_registration_number_normalization() -> None:
    assert normalize_registration_number("MH-12-AB-1234") == "MH12AB1234"
    assert normalize_registration_number(" mh 12 ab 1234 ") == "MH12AB1234"
    assert normalize_registration_number("") is None
    assert normalize_registration_number(None) is None
