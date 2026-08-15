from dataclasses import replace
from uuid import uuid4

import pytest

from domain.vehicle.entities import Vehicle
from domain.vehicle.exceptions import InvalidVehicleTransition
from domain.vehicle.states import VehicleStatus
from domain.vehicle.transitions import ALLOWED_TRANSITIONS, can_transition


def _vehicle(
    *,
    status: VehicleStatus = VehicleStatus.DRAFT,
    registration: str | None = "MH12AB1234",
) -> Vehicle:
    vehicle = Vehicle.create(
        tenant_id=uuid4(),
        fleet_id=uuid4(),
        registration_number=registration,
    )
    if status is VehicleStatus.DRAFT:
        return vehicle
    return replace(vehicle, vehicle_status=status)


def test_every_status_has_declared_transitions() -> None:
    assert set(ALLOWED_TRANSITIONS) == set(VehicleStatus)


def test_all_declared_transitions_are_allowed() -> None:
    for current, targets in ALLOWED_TRANSITIONS.items():
        for target in targets:
            assert can_transition(current, target)


def test_forbidden_transition_raises() -> None:
    vehicle = _vehicle(status=VehicleStatus.DRAFT)
    with pytest.raises(InvalidVehicleTransition, match="DRAFT to APPROVED"):
        vehicle.transition_to(VehicleStatus.APPROVED)


def test_submit_requires_registration() -> None:
    vehicle = _vehicle(registration=None)
    with pytest.raises(ValueError, match="registration"):
        vehicle.submit()


def test_submit_moves_draft_to_submitted() -> None:
    vehicle = _vehicle()
    submitted = vehicle.submit()
    assert submitted.vehicle_status is VehicleStatus.SUBMITTED


def test_create_starts_in_draft() -> None:
    vehicle = Vehicle.create(tenant_id=uuid4(), fleet_id=uuid4())
    assert vehicle.vehicle_status is VehicleStatus.DRAFT


def test_same_status_is_not_allowed() -> None:
    vehicle = _vehicle(status=VehicleStatus.DRAFT)
    with pytest.raises(InvalidVehicleTransition):
        vehicle.transition_to(VehicleStatus.DRAFT)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (VehicleStatus.DRAFT, VehicleStatus.SUBMITTED),
        (VehicleStatus.DRAFT, VehicleStatus.REJECTED),
        (VehicleStatus.SUBMITTED, VehicleStatus.VERIFICATION_PENDING),
        (VehicleStatus.SUBMITTED, VehicleStatus.DRAFT),
        (VehicleStatus.VERIFICATION_PENDING, VehicleStatus.VERIFIED),
        (VehicleStatus.VERIFICATION_PENDING, VehicleStatus.MANUAL_REVIEW),
        (VehicleStatus.VERIFIED, VehicleStatus.ENRICHMENT_PENDING),
        (VehicleStatus.VERIFIED, VehicleStatus.MANUAL_REVIEW),
        (VehicleStatus.ENRICHMENT_PENDING, VehicleStatus.READY_FOR_REVIEW),
        (VehicleStatus.ENRICHMENT_PENDING, VehicleStatus.MANUAL_REVIEW),
        (VehicleStatus.READY_FOR_REVIEW, VehicleStatus.APPROVED),
        (VehicleStatus.READY_FOR_REVIEW, VehicleStatus.MANUAL_REVIEW),
        (VehicleStatus.READY_FOR_REVIEW, VehicleStatus.REJECTED),
        (VehicleStatus.MANUAL_REVIEW, VehicleStatus.APPROVED),
        (VehicleStatus.MANUAL_REVIEW, VehicleStatus.REJECTED),
        (VehicleStatus.MANUAL_REVIEW, VehicleStatus.DRAFT),
        (VehicleStatus.MANUAL_REVIEW, VehicleStatus.VERIFICATION_PENDING),
        (VehicleStatus.APPROVED, VehicleStatus.SUSPENDED),
        (VehicleStatus.REJECTED, VehicleStatus.DRAFT),
        (VehicleStatus.SUSPENDED, VehicleStatus.APPROVED),
        (VehicleStatus.SUSPENDED, VehicleStatus.DRAFT),
    ],
)
def test_happy_path_edges(current: VehicleStatus, target: VehicleStatus) -> None:
    vehicle = _vehicle(status=current)
    next_vehicle = vehicle.transition_to(target)
    assert next_vehicle.vehicle_status is target
    assert next_vehicle.id == vehicle.id
