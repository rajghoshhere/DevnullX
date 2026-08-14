from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID

from domain.enrichment.models import Rule, VehicleAttributeProvenance
from domain.fleet.entities import Fleet
from domain.owner.entities import FleetOwner
from domain.tenant.entities import Tenant
from domain.truck.entities import Manufacturer, TruckModel
from domain.truck.taxonomy import TaxonomyTerm
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


class TaxonomyRepository(Protocol):
    async def add(self, table_name: str, term: TaxonomyTerm) -> TaxonomyTerm: ...

    async def get_by_code(self, table_name: str, code: str) -> TaxonomyTerm | None: ...

    async def get_by_id(self, table_name: str, term_id: UUID) -> TaxonomyTerm | None: ...

    async def list_active(self, table_name: str) -> list[TaxonomyTerm]: ...


class VehicleRepository(Protocol):
    async def add(self, vehicle: Vehicle) -> Vehicle: ...

    async def get_by_id(self, vehicle_id: UUID) -> Vehicle | None: ...

    async def get_by_normalized_registration(
        self,
        tenant_id: UUID,
        normalized_registration_number: str,
    ) -> Vehicle | None: ...

    async def update(self, vehicle: Vehicle) -> Vehicle: ...


class RuleRepository(Protocol):
    async def add(self, rule: Rule) -> Rule: ...

    async def list_effective(self, *, at: datetime) -> Sequence[Rule]: ...


class ProvenanceRepository(Protocol):
    async def add(self, row: VehicleAttributeProvenance) -> VehicleAttributeProvenance: ...

    async def list_for_vehicle(self, vehicle_id: UUID) -> Sequence[VehicleAttributeProvenance]: ...
