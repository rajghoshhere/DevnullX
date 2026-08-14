from __future__ import annotations

from uuid import UUID

from application.errors import NotFoundError
from domain.fleet.entities import Fleet
from domain.owner.entities import FleetOwner
from domain.vehicle.entities import Vehicle
from ports.repositories import FleetOwnerRepository, FleetRepository, VehicleRepository


class GetFleetOwner:
    def __init__(self, owners: FleetOwnerRepository) -> None:
        self._owners = owners

    async def execute(self, *, tenant_id: UUID, owner_id: UUID) -> FleetOwner:
        owner = await self._owners.get_by_id(owner_id)
        if owner is None or owner.tenant_id != tenant_id:
            raise NotFoundError("fleet owner not found")
        return owner


class GetFleet:
    def __init__(self, fleets: FleetRepository) -> None:
        self._fleets = fleets

    async def execute(self, *, tenant_id: UUID, fleet_id: UUID) -> Fleet:
        fleet = await self._fleets.get_by_id(fleet_id)
        if fleet is None or fleet.tenant_id != tenant_id:
            raise NotFoundError("fleet not found")
        return fleet


class GetVehicle:
    def __init__(self, vehicles: VehicleRepository) -> None:
        self._vehicles = vehicles

    async def execute(self, *, tenant_id: UUID, vehicle_id: UUID) -> Vehicle:
        vehicle = await self._vehicles.get_by_id(vehicle_id)
        if vehicle is None or vehicle.tenant_id != tenant_id:
            raise NotFoundError("vehicle not found")
        return vehicle
