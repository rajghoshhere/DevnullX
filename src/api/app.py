from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from adapters.postgres.session import dispose_engine
from api.middleware import RequestIdMiddleware
from api.routes.health import router as health_router
from config.logging import configure_logging
from config.settings import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    application = FastAPI(
        title="Fleet Owner & Truck Onboarding Platform",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.add_middleware(RequestIdMiddleware)
    application.include_router(health_router)
    return application
