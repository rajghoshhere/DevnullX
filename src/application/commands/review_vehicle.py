from __future__ import annotations

from uuid import UUID

from application.errors import InvalidStateError, NotFoundError
from domain.vehicle.entities import Vehicle
from domain.vehicle.exceptions import InvalidVehicleTransition
from domain.vehicle.states import VehicleStatus
from ports.repositories import VehicleRepository

_REVIEWABLE = frozenset({VehicleStatus.READY_FOR_REVIEW, VehicleStatus.MANUAL_REVIEW})


class ReviewVehicle:
    """Human confirmation after provider + rules have filled the record."""

    def __init__(self, vehicles: VehicleRepository) -> None:
        self._vehicles = vehicles

    async def execute(
        self,
        *,
        tenant_id: UUID,
        vehicle_id: UUID,
        decision: str,
    ) -> Vehicle:
        vehicle = await self._vehicles.get_by_id(vehicle_id)
        if vehicle is None or vehicle.tenant_id != tenant_id:
            raise NotFoundError("vehicle not found")
        if vehicle.vehicle_status not in _REVIEWABLE:
            raise InvalidStateError(f"vehicle cannot be reviewed from {vehicle.vehicle_status}")
        target = _target_status(decision)
        try:
            vehicle = vehicle.transition_to(target)
        except InvalidVehicleTransition as error:
            raise InvalidStateError(str(error)) from error
        return await self._vehicles.update(vehicle)


def _target_status(decision: str) -> VehicleStatus:
    normalized = decision.strip().upper()
    if normalized in {"APPROVE", "APPROVED"}:
        return VehicleStatus.APPROVED
    if normalized in {"REJECT", "REJECTED"}:
        return VehicleStatus.REJECTED
    raise InvalidStateError("decision must be APPROVE or REJECT")
