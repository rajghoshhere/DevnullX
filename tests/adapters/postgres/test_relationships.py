from sqlalchemy import select
from sqlalchemy.orm import selectinload

from adapters.postgres.models import (
    FleetModel,
    ManufacturerModel,
    TenantModel,
    TruckModelRecord,
)
from tests.adapters.postgres.helpers import seed_graph


async def test_tenant_owns_fleet_owners_and_fleets(db_session) -> None:
    tenant, owner, fleet, *_ = await seed_graph(db_session)

    loaded = (
        await db_session.execute(
            select(TenantModel)
            .options(
                selectinload(TenantModel.fleet_owners),
                selectinload(TenantModel.fleets),
            )
            .where(TenantModel.id == tenant.id)
        )
    ).scalar_one()

    assert [item.id for item in loaded.fleet_owners] == [owner.id]
    assert [item.id for item in loaded.fleets] == [fleet.id]


async def test_fleet_has_many_vehicles_and_vehicle_belongs_to_fleet(db_session) -> None:
    _tenant, _owner, fleet, _manufacturer, truck_model, vehicle = await seed_graph(db_session)

    loaded_fleet = (
        await db_session.execute(
            select(FleetModel)
            .options(selectinload(FleetModel.vehicles))
            .where(FleetModel.id == fleet.id)
        )
    ).scalar_one()

    assert len(loaded_fleet.vehicles) == 1
    loaded_vehicle = loaded_fleet.vehicles[0]
    assert loaded_vehicle.id == vehicle.id
    assert loaded_vehicle.tenant_id == fleet.tenant_id
    assert loaded_vehicle.fleet_id == fleet.id
    assert loaded_vehicle.truck_model_id == truck_model.id


async def test_manufacturer_has_many_truck_models_and_models_have_vehicles(db_session) -> None:
    _tenant, _owner, _fleet, manufacturer, truck_model, vehicle = await seed_graph(db_session)

    loaded_manufacturer = (
        await db_session.execute(
            select(ManufacturerModel)
            .options(selectinload(ManufacturerModel.truck_models))
            .where(ManufacturerModel.id == manufacturer.id)
        )
    ).scalar_one()
    assert [item.id for item in loaded_manufacturer.truck_models] == [truck_model.id]

    loaded_model = (
        await db_session.execute(
            select(TruckModelRecord)
            .options(selectinload(TruckModelRecord.vehicles))
            .where(TruckModelRecord.id == truck_model.id)
        )
    ).scalar_one()
    assert [item.id for item in loaded_model.vehicles] == [vehicle.id]
