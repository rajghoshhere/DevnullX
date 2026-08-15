from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from domain.enrichment.models import Rule, VehicleAttributeProvenance
from domain.fleet.entities import Fleet
from domain.owner.entities import FleetOwner
from domain.tenant.entities import Tenant
from domain.vehicle.entities import Vehicle


class InMemoryTenantRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, Tenant] = {}

    async def add(self, tenant: Tenant) -> Tenant:
        self.items[tenant.id] = tenant
        return tenant

    async def get_by_id(self, tenant_id: UUID) -> Tenant | None:
        return self.items.get(tenant_id)


class InMemoryFleetOwnerRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, FleetOwner] = {}

    async def add(self, owner: FleetOwner) -> FleetOwner:
        self.items[owner.id] = owner
        return owner

    async def get_by_id(self, owner_id: UUID) -> FleetOwner | None:
        return self.items.get(owner_id)


class InMemoryFleetRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, Fleet] = {}

    async def add(self, fleet: Fleet) -> Fleet:
        self.items[fleet.id] = fleet
        return fleet

    async def get_by_id(self, fleet_id: UUID) -> Fleet | None:
        return self.items.get(fleet_id)


class InMemoryVehicleRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, Vehicle] = {}

    async def add(self, vehicle: Vehicle) -> Vehicle:
        self.items[vehicle.id] = vehicle
        return vehicle

    async def get_by_id(self, vehicle_id: UUID) -> Vehicle | None:
        return self.items.get(vehicle_id)

    async def get_by_normalized_registration(
        self,
        tenant_id: UUID,
        normalized_registration_number: str,
    ) -> Vehicle | None:
        for vehicle in self.items.values():
            if (
                vehicle.tenant_id == tenant_id
                and vehicle.normalized_registration_number == normalized_registration_number
            ):
                return vehicle
        return None

    async def update(self, vehicle: Vehicle) -> Vehicle:
        if vehicle.id not in self.items:
            raise ValueError("vehicle not found")
        self.items[vehicle.id] = vehicle
        return vehicle


class InMemoryRuleRepository:
    def __init__(self, rules: Sequence[Rule] | None = None) -> None:
        self.items: list[Rule] = list(rules or [])

    async def add(self, rule: Rule) -> Rule:
        self.items.append(rule)
        return rule

    async def list_effective(self, *, at: datetime) -> Sequence[Rule]:
        return [rule for rule in self.items if rule.is_effective_at(at)]


class InMemoryProvenanceRepository:
    def __init__(self) -> None:
        self.items: list[VehicleAttributeProvenance] = []

    async def add(self, row: VehicleAttributeProvenance) -> VehicleAttributeProvenance:
        self.items.append(row)
        return row

    async def list_for_vehicle(self, vehicle_id: UUID) -> Sequence[VehicleAttributeProvenance]:
        return [row for row in self.items if row.vehicle_id == vehicle_id]


async def seed_tenant_and_fleet(
    tenants: InMemoryTenantRepository | None = None,
    fleets: InMemoryFleetRepository | None = None,
    *,
    tenant_name: str = "Acme Logistics",
    fleet_name: str = "North Fleet",
) -> tuple[Tenant, Fleet, InMemoryTenantRepository, InMemoryFleetRepository]:
    tenant_repo = tenants or InMemoryTenantRepository()
    fleet_repo = fleets or InMemoryFleetRepository()
    tenant = Tenant.create(tenant_name)
    fleet = Fleet.create(tenant_id=tenant.id, name=fleet_name)
    await tenant_repo.add(tenant)
    await fleet_repo.add(fleet)
    return tenant, fleet, tenant_repo, fleet_repo
