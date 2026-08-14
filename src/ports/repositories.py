from __future__ import annotations

from typing import Protocol
from uuid import UUID

from domain.fleet.entities import Fleet
from domain.owner.entities import FleetOwner
from domain.tenant.entities import Tenant
from domain.truck.entities import Manufacturer, TruckModel
from domain.vehicle.entities import Vehicle


class TenantRepository(Protocol):
    async def add(self, tenant: Tenant) -> Tenant: ...

    async def get_by_id(self, tenant_id: UUID) -> Tenant | None: ...


class FleetOwnerRepository(Protocol):
    async def add(self, owner: FleetOwner) -> FleetOwner: ...

    async def get_by_id(self, owner_id: UUID) -> FleetOwner | None: ...


class FleetRepository(Protocol):
    async def add(self, fleet: Fleet) -> Fleet: ...

    async def get_by_id(self, fleet_id: UUID) -> Fleet | None: ...


class ManufacturerRepository(Protocol):
    async def add(self, manufacturer: Manufacturer) -> Manufacturer: ...

    async def get_by_id(self, manufacturer_id: UUID) -> Manufacturer | None: ...


class TruckModelRepository(Protocol):
    async def add(self, truck_model: TruckModel) -> TruckModel: ...

    async def get_by_id(self, truck_model_id: UUID) -> TruckModel | None: ...


class VehicleRepository(Protocol):
    async def add(self, vehicle: Vehicle) -> Vehicle: ...

    async def get_by_id(self, vehicle_id: UUID) -> Vehicle | None: ...

    async def get_by_normalized_registration(
        self,
        tenant_id: UUID,
        normalized_registration_number: str,
    ) -> Vehicle | None: ...
