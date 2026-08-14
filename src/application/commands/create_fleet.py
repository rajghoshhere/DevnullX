from __future__ import annotations

from uuid import UUID

from application.errors import NotFoundError
from domain.fleet.entities import Fleet
from ports.repositories import FleetRepository, TenantRepository


class CreateFleet:
    def __init__(self, tenants: TenantRepository, fleets: FleetRepository) -> None:
        self._tenants = tenants
        self._fleets = fleets

    async def execute(self, *, tenant_id: UUID, name: str) -> Fleet:
        tenant = await self._tenants.get_by_id(tenant_id)
        if tenant is None:
            raise NotFoundError("tenant not found")
        fleet = Fleet.create(tenant_id=tenant.id, name=name)
        return await self._fleets.add(fleet)
