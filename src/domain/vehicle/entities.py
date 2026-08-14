from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID, uuid4

from domain.tenant.entities import utc_now
from domain.vehicle.registration import normalize_registration_number
from domain.vehicle.states import VehicleStatus


@dataclass(frozen=True, slots=True)
class Vehicle:
    id: UUID
    tenant_id: UUID
    fleet_id: UUID
    truck_model_id: UUID | None
    registration_number: str | None
    normalized_registration_number: str | None
    registration_date: date | None
    manufacturing_month_year: date | None
    gvw_kg: int | None
    unladen_weight_kg: int | None
    engine_cc: int | None
    cylinder_count: int | None
    fuel_type: str | None
    body_type: str | None
    vehicle_status: VehicleStatus
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def create(
        *,
        tenant_id: UUID,
        fleet_id: UUID,
        truck_model_id: UUID | None = None,
        registration_number: str | None = None,
        registration_date: date | None = None,
        manufacturing_month_year: date | None = None,
        gvw_kg: int | None = None,
        unladen_weight_kg: int | None = None,
        engine_cc: int | None = None,
        cylinder_count: int | None = None,
        fuel_type: str | None = None,
        body_type: str | None = None,
        vehicle_status: VehicleStatus = VehicleStatus.DRAFT,
    ) -> Vehicle:
        now = utc_now()
        return Vehicle(
            id=uuid4(),
            tenant_id=tenant_id,
            fleet_id=fleet_id,
            truck_model_id=truck_model_id,
            registration_number=registration_number,
            normalized_registration_number=normalize_registration_number(registration_number),
            registration_date=registration_date,
            manufacturing_month_year=manufacturing_month_year,
            gvw_kg=gvw_kg,
            unladen_weight_kg=unladen_weight_kg,
            engine_cc=engine_cc,
            cylinder_count=cylinder_count,
            fuel_type=fuel_type,
            body_type=body_type,
            vehicle_status=vehicle_status,
            created_at=now,
            updated_at=now,
        )
