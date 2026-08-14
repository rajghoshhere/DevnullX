from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.postgres.mappers import fleet_to_domain, fleet_to_model
from adapters.postgres.models import FleetModel
from domain.fleet.entities import Fleet


class PostgresFleetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, fleet: Fleet) -> Fleet:
        self._session.add(fleet_to_model(fleet))
        await self._session.flush()
        return fleet

    async def get_by_id(self, fleet_id: UUID) -> Fleet | None:
        result = await self._session.execute(select(FleetModel).where(FleetModel.id == fleet_id))
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return fleet_to_domain(model)
