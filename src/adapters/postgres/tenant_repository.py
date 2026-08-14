from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.postgres.mappers import tenant_to_domain, tenant_to_model
from adapters.postgres.models import TenantModel
from domain.tenant.entities import Tenant


class PostgresTenantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, tenant: Tenant) -> Tenant:
        self._session.add(tenant_to_model(tenant))
        await self._session.flush()
        return tenant

    async def get_by_id(self, tenant_id: UUID) -> Tenant | None:
        result = await self._session.execute(
            select(TenantModel).where(TenantModel.id == tenant_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return tenant_to_domain(model)
