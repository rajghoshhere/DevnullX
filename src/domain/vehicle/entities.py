from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
from uuid import UUID, uuid4

from domain.tenant.entities import utc_now
from domain.vehicle.exceptions import InvalidVehicleTransition
from domain.vehicle.registration import normalize_registration_number
from domain.vehicle.states import VehicleStatus
from domain.vehicle.transitions import can_transition
from domain.verification.types import VerifiedVehicleAttributes


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
            vehicle_status=VehicleStatus.DRAFT,
            created_at=now,
            updated_at=now,
        )

    def capture_registration(self, registration_number: str) -> Vehicle:
        stripped = registration_number.strip()
        if not stripped:
            raise ValueError("registration number is required")
        return replace(
            self,
            registration_number=stripped,
            normalized_registration_number=normalize_registration_number(stripped),
            updated_at=utc_now(),
        )

    def transition_to(self, target: VehicleStatus) -> Vehicle:
        if not can_transition(self.vehicle_status, target):
            raise InvalidVehicleTransition(self.vehicle_status, target)
        return replace(self, vehicle_status=target, updated_at=utc_now())

    def submit(self) -> Vehicle:
        if not self.registration_number:
            raise ValueError("registration number is required to submit a vehicle")
        return self.transition_to(VehicleStatus.SUBMITTED)

    def apply_verified_attributes(self, attributes: VerifiedVehicleAttributes) -> Vehicle:
        return replace(
            self,
            registration_date=attributes.registration_date or self.registration_date,
            manufacturing_month_year=(
                attributes.manufacturing_month_year or self.manufacturing_month_year
            ),
            gvw_kg=attributes.gvw_kg if attributes.gvw_kg is not None else self.gvw_kg,
            unladen_weight_kg=(
                attributes.unladen_weight_kg
                if attributes.unladen_weight_kg is not None
                else self.unladen_weight_kg
            ),
            engine_cc=attributes.engine_cc if attributes.engine_cc is not None else self.engine_cc,
            cylinder_count=(
                attributes.cylinder_count
                if attributes.cylinder_count is not None
                else self.cylinder_count
            ),
            fuel_type=attributes.fuel_type or self.fuel_type,
            body_type=attributes.body_type or self.body_type,
            updated_at=utc_now(),
        )
