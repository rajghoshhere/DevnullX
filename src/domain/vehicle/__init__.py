from domain.vehicle.entities import Vehicle
from domain.vehicle.registration import normalize_registration_number
from domain.vehicle.states import VehicleStatus
from domain.vehicle.taxonomy import BodyType, FuelType

__all__ = [
    "BodyType",
    "FuelType",
    "Vehicle",
    "VehicleStatus",
    "normalize_registration_number",
]
