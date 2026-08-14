from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.postgres.mappers import fleet_owner_to_domain, fleet_owner_to_model
from adapters.postgres.models import FleetOwnerModel
from domain.owner.entities import FleetOwner


class PostgresFleetOwnerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, owner: FleetOwner) -> FleetOwner:
        self._session.add(fleet_owner_to_model(owner))
        await self._session.flush()
        return owner

    async def get_by_id(self, owner_id: UUID) -> FleetOwner | None:
        result = await self._session.execute(
            select(FleetOwnerModel).where(FleetOwnerModel.id == owner_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return fleet_owner_to_domain(model)
