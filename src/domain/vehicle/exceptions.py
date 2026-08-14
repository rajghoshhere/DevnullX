from domain.vehicle.states import VehicleStatus


class InvalidVehicleTransition(Exception):
    def __init__(self, current: VehicleStatus, target: VehicleStatus) -> None:
        self.current = current
        self.target = target
        super().__init__(f"cannot transition vehicle from {current} to {target}")
