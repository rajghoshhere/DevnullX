from domain.vehicle.entities import Vehicle
from domain.vehicle.exceptions import InvalidVehicleTransition
from domain.vehicle.registration import normalize_registration_number
from domain.vehicle.states import VehicleStatus
from domain.vehicle.transitions import ALLOWED_TRANSITIONS, can_transition

__all__ = [
    "ALLOWED_TRANSITIONS",
    "InvalidVehicleTransition",
    "Vehicle",
    "VehicleStatus",
    "can_transition",
    "normalize_registration_number",
]
