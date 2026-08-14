from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.postgres.mappers import manufacturer_to_domain, manufacturer_to_model
from adapters.postgres.models import ManufacturerModel
from domain.truck.entities import Manufacturer


class PostgresManufacturerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, manufacturer: Manufacturer) -> Manufacturer:
        self._session.add(manufacturer_to_model(manufacturer))
        await self._session.flush()
        return manufacturer

    async def get_by_id(self, manufacturer_id: UUID) -> Manufacturer | None:
        result = await self._session.execute(
            select(ManufacturerModel).where(ManufacturerModel.id == manufacturer_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return manufacturer_to_domain(model)
