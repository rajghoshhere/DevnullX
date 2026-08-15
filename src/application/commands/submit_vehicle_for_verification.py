from __future__ import annotations

from uuid import UUID, uuid4

from application.errors import ConflictError, InvalidStateError, NotFoundError
from domain.vehicle.entities import Vehicle
from domain.vehicle.exceptions import InvalidVehicleTransition
from domain.vehicle.registration import normalize_registration_number
from domain.vehicle.states import VehicleStatus
from domain.verification.types import VerificationContext
from ports.repositories import VehicleRepository
from ports.vehicle_provider import VehicleVerificationProvider


class SubmitVehicleForVerification:
    def __init__(
        self,
        vehicles: VehicleRepository,
        verification_provider: VehicleVerificationProvider,
    ) -> None:
        self._vehicles = vehicles
        self._verification_provider = verification_provider

    async def execute(
        self,
        *,
        tenant_id: UUID,
        vehicle_id: UUID,
        registration_number: str | None = None,
    ) -> Vehicle:
        vehicle = await self._vehicles.get_by_id(vehicle_id)
        if vehicle is None or vehicle.tenant_id != tenant_id:
            raise NotFoundError("vehicle not found")
        if registration_number:
            vehicle = vehicle.capture_registration(registration_number)
            await self._assert_registration_available(vehicle)
        try:
            if vehicle.vehicle_status is VehicleStatus.DRAFT:
                vehicle = vehicle.submit().transition_to(VehicleStatus.VERIFICATION_PENDING)
            elif vehicle.vehicle_status is VehicleStatus.SUBMITTED:
                vehicle = vehicle.transition_to(VehicleStatus.VERIFICATION_PENDING)
            else:
                raise InvalidStateError(
                    f"vehicle cannot be submitted from {vehicle.vehicle_status}"
                )
        except InvalidVehicleTransition as error:
            raise InvalidStateError(str(error)) from error
        except ValueError as error:
            raise InvalidStateError(str(error)) from error

        vehicle = await self._vehicles.update(vehicle)
        if vehicle.registration_number is None:
            raise InvalidStateError("registration number is required to submit a vehicle")

        result = await self._verification_provider.verify_registration(
            vehicle.registration_number,
            VerificationContext(
                tenant_id=vehicle.tenant_id,
                vehicle_id=vehicle.id,
                correlation_id=str(uuid4()),
                registration_number=vehicle.registration_number,
            ),
        )
        if result.attributes is not None:
            vehicle = vehicle.apply_verified_attributes(result.attributes)
        target = VehicleStatus.VERIFIED if result.success else VehicleStatus.MANUAL_REVIEW
        try:
            vehicle = vehicle.transition_to(target)
        except InvalidVehicleTransition as error:
            raise InvalidStateError(str(error)) from error
        return await self._vehicles.update(vehicle)

    async def _assert_registration_available(self, vehicle: Vehicle) -> None:
        normalized = normalize_registration_number(vehicle.registration_number)
        if normalized is None:
            return
        existing = await self._vehicles.get_by_normalized_registration(
            vehicle.tenant_id, normalized
        )
        if existing is not None and existing.id != vehicle.id:
            raise ConflictError("a vehicle with this registration number already exists")
