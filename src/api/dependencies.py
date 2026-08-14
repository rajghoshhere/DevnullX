from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.postgres.session import get_db_session
from adapters.postgres.tenant_repository import PostgresTenantRepository
from adapters.postgres.vehicle_repository import PostgresVehicleRepository
from ports.repositories import TenantRepository, VehicleRepository

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_tenant_repository(session: DbSession) -> AsyncIterator[TenantRepository]:
    yield PostgresTenantRepository(session)


async def get_vehicle_repository(session: DbSession) -> AsyncIterator[VehicleRepository]:
    yield PostgresVehicleRepository(session)
