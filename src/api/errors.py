from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from application.errors import ConflictError, InvalidStateError, NotFoundError
from domain.vehicle.exceptions import InvalidVehicleTransition


def register_error_handlers(application: FastAPI) -> None:
    @application.exception_handler(NotFoundError)
    async def not_found(_request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @application.exception_handler(ConflictError)
    async def conflict(_request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @application.exception_handler(InvalidStateError)
    async def invalid_state(_request: Request, exc: InvalidStateError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @application.exception_handler(InvalidVehicleTransition)
    async def invalid_transition(
        _request: Request, exc: InvalidVehicleTransition
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})
