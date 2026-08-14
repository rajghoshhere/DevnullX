from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.postgres.mappers import truck_model_to_domain, truck_model_to_record
from adapters.postgres.models import TruckModelRecord
from domain.truck.entities import TruckModel


class PostgresTruckModelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, truck_model: TruckModel) -> TruckModel:
        self._session.add(truck_model_to_record(truck_model))
        await self._session.flush()
        return truck_model

    async def get_by_id(self, truck_model_id: UUID) -> TruckModel | None:
        result = await self._session.execute(
            select(TruckModelRecord).where(TruckModelRecord.id == truck_model_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return truck_model_to_domain(model)
