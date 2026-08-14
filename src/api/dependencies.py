from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.postgres.session import get_db_session
from adapters.postgres.tenant_repository import PostgresTenantRepository
from ports.repositories import TenantRepository

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_tenant_repository(session: DbSession) -> AsyncIterator[TenantRepository]:
    yield PostgresTenantRepository(session)
