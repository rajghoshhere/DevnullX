from domain.vehicle.states import VehicleStatus

ALLOWED_TRANSITIONS: dict[VehicleStatus, frozenset[VehicleStatus]] = {
    VehicleStatus.DRAFT: frozenset({VehicleStatus.SUBMITTED, VehicleStatus.REJECTED}),
    VehicleStatus.SUBMITTED: frozenset(
        {VehicleStatus.VERIFICATION_PENDING, VehicleStatus.DRAFT}
    ),
    VehicleStatus.VERIFICATION_PENDING: frozenset(
        {VehicleStatus.VERIFIED, VehicleStatus.MANUAL_REVIEW}
    ),
    VehicleStatus.VERIFIED: frozenset(
        {VehicleStatus.ENRICHMENT_PENDING, VehicleStatus.MANUAL_REVIEW}
    ),
    VehicleStatus.ENRICHMENT_PENDING: frozenset(
        {VehicleStatus.READY_FOR_REVIEW, VehicleStatus.MANUAL_REVIEW}
    ),
    VehicleStatus.READY_FOR_REVIEW: frozenset(
        {
            VehicleStatus.APPROVED,
            VehicleStatus.MANUAL_REVIEW,
            VehicleStatus.REJECTED,
        }
    ),
    VehicleStatus.MANUAL_REVIEW: frozenset(
        {VehicleStatus.APPROVED, VehicleStatus.REJECTED, VehicleStatus.DRAFT}
    ),
    VehicleStatus.APPROVED: frozenset({VehicleStatus.SUSPENDED}),
    VehicleStatus.REJECTED: frozenset({VehicleStatus.DRAFT}),
    VehicleStatus.SUSPENDED: frozenset({VehicleStatus.APPROVED, VehicleStatus.DRAFT}),
}


def can_transition(current: VehicleStatus, target: VehicleStatus) -> bool:
    return target in ALLOWED_TRANSITIONS[current]
