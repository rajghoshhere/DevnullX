from fastapi import APIRouter

from adapters.postgres.health import ping_database
from api.dependencies import DbSession
from api.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(session: DbSession) -> HealthResponse:
    await ping_database(session)
    return HealthResponse(status="ok")
