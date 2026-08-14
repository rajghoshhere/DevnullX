from datetime import date

from adapters.postgres.fleet_owner_repository import PostgresFleetOwnerRepository
from adapters.postgres.fleet_repository import PostgresFleetRepository
from adapters.postgres.manufacturer_repository import PostgresManufacturerRepository
from adapters.postgres.tenant_repository import PostgresTenantRepository
from adapters.postgres.truck_model_repository import PostgresTruckModelRepository
from adapters.postgres.vehicle_repository import PostgresVehicleRepository
from domain.fleet.entities import Fleet
from domain.owner.entities import FleetOwner
from domain.tenant.entities import Tenant
from domain.truck.entities import Manufacturer, TruckModel
from domain.vehicle.entities import Vehicle
from domain.vehicle.states import VehicleStatus


async def seed_graph(db_session, *, registration_number: str = "MH12AB1234"):
    tenant = Tenant.create("Acme Logistics")
    owner = FleetOwner.create(tenant_id=tenant.id, name="Priya Shah")
    fleet = Fleet.create(tenant_id=tenant.id, name="West Fleet")
    manufacturer = Manufacturer.create("Tata Motors")
    truck_model = TruckModel.create(manufacturer_id=manufacturer.id, name="Signa 4825.T")
    vehicle = Vehicle.create(
        tenant_id=tenant.id,
        fleet_id=fleet.id,
        truck_model_id=truck_model.id,
        registration_number=registration_number,
        registration_date=date(2022, 3, 15),
        manufacturing_month_year=date(2022, 1, 1),
        gvw_kg=47500,
        unladen_weight_kg=12500,
        engine_cc=6700,
        cylinder_count=6,
        fuel_type="DIESEL",
        body_type="OPEN",
        vehicle_status=VehicleStatus.DRAFT,
    )

    await PostgresTenantRepository(db_session).add(tenant)
    await PostgresFleetOwnerRepository(db_session).add(owner)
    await PostgresFleetRepository(db_session).add(fleet)
    await PostgresManufacturerRepository(db_session).add(manufacturer)
    await PostgresTruckModelRepository(db_session).add(truck_model)
    await PostgresVehicleRepository(db_session).add(vehicle)
    await db_session.flush()
    return tenant, owner, fleet, manufacturer, truck_model, vehicle
