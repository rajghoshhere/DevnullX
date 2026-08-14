from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.postgres.mappers import vehicle_to_domain, vehicle_to_model
from adapters.postgres.models import VehicleModel
from domain.vehicle.entities import Vehicle


class PostgresVehicleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, vehicle: Vehicle) -> Vehicle:
        self._session.add(vehicle_to_model(vehicle))
        await self._session.flush()
        return vehicle

    async def get_by_id(self, vehicle_id: UUID) -> Vehicle | None:
        result = await self._session.execute(
            select(VehicleModel).where(VehicleModel.id == vehicle_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return vehicle_to_domain(model)

    async def get_by_normalized_registration(
        self,
        tenant_id: UUID,
        normalized_registration_number: str,
    ) -> Vehicle | None:
        result = await self._session.execute(
            select(VehicleModel).where(
                VehicleModel.tenant_id == tenant_id,
                VehicleModel.normalized_registration_number == normalized_registration_number,
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return vehicle_to_domain(model)
