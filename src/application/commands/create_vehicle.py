from __future__ import annotations

from datetime import date
from uuid import UUID

from application.errors import ConflictError, NotFoundError
from domain.vehicle.entities import Vehicle
from domain.vehicle.registration import normalize_registration_number
from ports.repositories import FleetRepository, TenantRepository, VehicleRepository


class CreateVehicle:
    def __init__(
        self,
        tenants: TenantRepository,
        fleets: FleetRepository,
        vehicles: VehicleRepository,
    ) -> None:
        self._tenants = tenants
        self._fleets = fleets
        self._vehicles = vehicles

    async def execute(
        self,
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
        tenant = await self._tenants.get_by_id(tenant_id)
        if tenant is None:
            raise NotFoundError("tenant not found")
        fleet = await self._fleets.get_by_id(fleet_id)
        if fleet is None or fleet.tenant_id != tenant.id:
            raise NotFoundError("fleet not found")
        await self._assert_registration_available(tenant.id, registration_number)
        vehicle = Vehicle.create(
            tenant_id=tenant.id,
            fleet_id=fleet.id,
            truck_model_id=truck_model_id,
            registration_number=registration_number,
            registration_date=registration_date,
            manufacturing_month_year=manufacturing_month_year,
            gvw_kg=gvw_kg,
            unladen_weight_kg=unladen_weight_kg,
            engine_cc=engine_cc,
            cylinder_count=cylinder_count,
            fuel_type=fuel_type,
            body_type=body_type,
        )
        return await self._vehicles.add(vehicle)

    async def _assert_registration_available(
        self, tenant_id: UUID, registration_number: str | None
    ) -> None:
        normalized = normalize_registration_number(registration_number)
        if normalized is None:
            return
        existing = await self._vehicles.get_by_normalized_registration(tenant_id, normalized)
        if existing is not None:
            raise ConflictError("a vehicle with this registration number already exists")
