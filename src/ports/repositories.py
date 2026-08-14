from __future__ import annotations

from typing import Protocol
from uuid import UUID

from domain.tenant.entities import Tenant


class TenantRepository(Protocol):
    async def add(self, tenant: Tenant) -> Tenant: ...

    async def get_by_id(self, tenant_id: UUID) -> Tenant | None: ...
