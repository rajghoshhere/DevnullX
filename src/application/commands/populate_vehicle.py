from __future__ import annotations

from dataclasses import replace
from uuid import UUID, uuid4

from application.errors import ConflictError, InvalidStateError, NotFoundError
from domain.enrichment.engine import RuleEngine
from domain.enrichment.models import VehicleAttributeProvenance, VehicleFacts
from domain.tenant.entities import utc_now
from domain.vehicle.entities import Vehicle
from domain.vehicle.exceptions import InvalidVehicleTransition
from domain.vehicle.registration import normalize_registration_number
from domain.vehicle.states import VehicleStatus
from domain.verification.types import VerificationContext
from ports.repositories import ProvenanceRepository, RuleRepository, VehicleRepository
from ports.vehicle_provider import VehicleVerificationProvider

_MAPPABLE_VEHICLE_ATTRIBUTES = frozenset({"body_type", "fuel_type"})


class PopulateVehicle:
    """Fill a draft from the vehicle provider and deterministic rules.

    Humans do not enter RC fields. They only review the result later.
    """

    def __init__(
        self,
        vehicles: VehicleRepository,
        verification_provider: VehicleVerificationProvider,
        rules: RuleRepository,
        provenance: ProvenanceRepository,
        engine: RuleEngine | None = None,
    ) -> None:
        self._vehicles = vehicles
        self._verification_provider = verification_provider
        self._rules = rules
        self._provenance = provenance
        self._engine = engine or RuleEngine()

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
            vehicle = _begin_provider_fetch(vehicle)
        except InvalidVehicleTransition as error:
            raise InvalidStateError(str(error)) from error
        except ValueError as error:
            raise InvalidStateError(str(error)) from error

        vehicle = await self._vehicles.update(vehicle)
        if vehicle.registration_number is None:
            raise InvalidStateError("registration number is required to populate a vehicle")

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
        if not result.success:
            vehicle = vehicle.transition_to(VehicleStatus.MANUAL_REVIEW)
            return await self._vehicles.update(vehicle)

        vehicle = vehicle.transition_to(VehicleStatus.VERIFIED).transition_to(
            VehicleStatus.ENRICHMENT_PENDING
        )
        vehicle = await self._apply_rules(vehicle)
        vehicle = vehicle.transition_to(VehicleStatus.READY_FOR_REVIEW)
        return await self._vehicles.update(vehicle)

    async def _apply_rules(self, vehicle: Vehicle) -> Vehicle:
        rules = await self._rules.list_effective(at=utc_now())
        results = self._engine.evaluate(rules, _facts_from_vehicle(vehicle))
        for result in results:
            if not result.applied or result.value is None:
                continue
            await self._provenance.add(
                VehicleAttributeProvenance.from_result(
                    tenant_id=vehicle.tenant_id,
                    vehicle_id=vehicle.id,
                    result=result,
                )
            )
            if result.attribute in _MAPPABLE_VEHICLE_ATTRIBUTES:
                vehicle = replace(vehicle, **{result.attribute: result.value}, updated_at=utc_now())
        return vehicle

    async def _assert_registration_available(self, vehicle: Vehicle) -> None:
        normalized = normalize_registration_number(vehicle.registration_number)
        if normalized is None:
            return
        existing = await self._vehicles.get_by_normalized_registration(
            vehicle.tenant_id, normalized
        )
        if existing is not None and existing.id != vehicle.id:
            raise ConflictError("a vehicle with this registration number already exists")


def _begin_provider_fetch(vehicle: Vehicle) -> Vehicle:
    if vehicle.vehicle_status is VehicleStatus.DRAFT:
        return vehicle.submit().transition_to(VehicleStatus.VERIFICATION_PENDING)
    if vehicle.vehicle_status is VehicleStatus.SUBMITTED:
        return vehicle.transition_to(VehicleStatus.VERIFICATION_PENDING)
    if vehicle.vehicle_status is VehicleStatus.MANUAL_REVIEW:
        return vehicle.transition_to(VehicleStatus.VERIFICATION_PENDING)
    raise InvalidVehicleTransition(vehicle.vehicle_status, VehicleStatus.VERIFICATION_PENDING)


def _facts_from_vehicle(vehicle: Vehicle) -> VehicleFacts:
    known: dict[str, str] = {}
    if vehicle.fuel_type:
        known["fuel_type"] = vehicle.fuel_type
    if vehicle.body_type:
        known["body_type"] = vehicle.body_type
    return VehicleFacts(
        gvw_kg=vehicle.gvw_kg,
        unladen_weight_kg=vehicle.unladen_weight_kg,
        raw_body_text=vehicle.body_type,
        raw_manufacturer=None,
        known_attributes=known,
    )


class SubmitVehicleForVerification(PopulateVehicle):
    """Backward-compatible name for PopulateVehicle."""
