from __future__ import annotations

from uuid import UUID

from application.errors import NotFoundError
from domain.owner.entities import FleetOwner
from domain.tenant.entities import Tenant
from ports.repositories import FleetOwnerRepository, TenantRepository


class CreateFleetOwner:
    def __init__(self, tenants: TenantRepository, owners: FleetOwnerRepository) -> None:
        self._tenants = tenants
        self._owners = owners

    async def execute(self, *, tenant_id: UUID, name: str) -> FleetOwner:
        tenant = await self._require_tenant(tenant_id)
        owner = FleetOwner.create(tenant_id=tenant.id, name=name)
        return await self._owners.add(owner)

    async def _require_tenant(self, tenant_id: UUID) -> Tenant:
        tenant = await self._tenants.get_by_id(tenant_id)
        if tenant is None:
            raise NotFoundError("tenant not found")
        return tenant
