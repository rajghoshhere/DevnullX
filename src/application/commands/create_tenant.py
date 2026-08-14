from __future__ import annotations

from domain.tenant.entities import Tenant
from ports.repositories import TenantRepository


class CreateTenant:
    def __init__(self, tenants: TenantRepository) -> None:
        self._tenants = tenants

    async def execute(self, *, name: str) -> Tenant:
        return await self._tenants.add(Tenant.create(name))
