from datetime import date

from adapters.postgres.vehicle_repository import PostgresVehicleRepository
from domain.vehicle.taxonomy import BodyType, FuelType
from tests.adapters.postgres.helpers import seed_graph


async def test_vehicle_repository_round_trip(db_session) -> None:
    _tenant, _owner, _fleet, _manufacturer, _truck_model, vehicle = await seed_graph(db_session)

    found = await PostgresVehicleRepository(db_session).get_by_id(vehicle.id)

    assert found is not None
    assert found.registration_number == "MH12AB1234"
    assert found.normalized_registration_number == "MH12AB1234"
    assert found.registration_date == date(2022, 3, 15)
    assert found.manufacturing_month_year == date(2022, 1, 1)
    assert found.gvw_kg == 47500
    assert found.unladen_weight_kg == 12500
    assert found.engine_cc == 6700
    assert found.cylinder_count == 6
    assert found.fuel_type == FuelType.DIESEL
    assert found.body_type == BodyType.OPEN
