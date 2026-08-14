from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.postgres.models import TenantModel
from domain.tenant.entities import Tenant


class PostgresTenantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, tenant: Tenant) -> Tenant:
        self._session.add(
            TenantModel(id=tenant.id, name=tenant.name, created_at=tenant.created_at)
        )
        await self._session.flush()
        return tenant

    async def get_by_id(self, tenant_id: UUID) -> Tenant | None:
        result = await self._session.execute(
            select(TenantModel).where(TenantModel.id == tenant_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return Tenant(id=model.id, name=model.name, created_at=model.created_at)
