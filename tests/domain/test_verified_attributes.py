from datetime import date
from uuid import uuid4

from domain.vehicle.entities import Vehicle
from domain.verification.types import VerifiedVehicleAttributes


def test_apply_verified_attributes_fills_canonical_fields() -> None:
    vehicle = Vehicle.create(tenant_id=uuid4(), fleet_id=uuid4())
    updated = vehicle.apply_verified_attributes(
        VerifiedVehicleAttributes(
            registration_date=date(2022, 3, 15),
            manufacturing_month_year=date(2022, 1, 1),
            gvw_kg=47500,
            unladen_weight_kg=12500,
            engine_cc=6700,
            cylinder_count=6,
            fuel_type="DIESEL",
            body_type="OPEN",
        )
    )
    assert updated.gvw_kg == 47500
    assert updated.fuel_type == "DIESEL"
    assert updated.registration_date == date(2022, 3, 15)


def test_apply_verified_attributes_does_not_clear_existing_values() -> None:
    vehicle = Vehicle.create(
        tenant_id=uuid4(),
        fleet_id=uuid4(),
        gvw_kg=16000,
        fuel_type="CNG",
    )
    updated = vehicle.apply_verified_attributes(VerifiedVehicleAttributes(body_type="OPEN"))
    assert updated.gvw_kg == 16000
    assert updated.fuel_type == "CNG"
    assert updated.body_type == "OPEN"
