from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from application.commands.populate_vehicle import PopulateVehicle
from application.errors import ApplicationError, BatchValidationError
from domain.vehicle.entities import Vehicle
from domain.vehicle.states import VehicleStatus

MAX_BATCH_SIZE = 100


@dataclass(frozen=True, slots=True)
class BatchPopulateItem:
    vehicle_id: UUID
    ok: bool
    vehicle: Vehicle | None
    detail: str | None


@dataclass(frozen=True, slots=True)
class BatchPopulateResult:
    items: tuple[BatchPopulateItem, ...]

    @property
    def requested(self) -> int:
        return len(self.items)

    @property
    def populated(self) -> int:
        return sum(
            1
            for item in self.items
            if item.vehicle is not None
            and item.vehicle.vehicle_status is VehicleStatus.READY_FOR_REVIEW
        )

    @property
    def verified(self) -> int:
        """Alias kept for older tests and clients."""
        return self.populated

    @property
    def failed(self) -> int:
        return sum(1 for item in self.items if not item.ok)


class PopulateVehiclesBatch:
    """Bulk-upload follow-up: fill many drafts from the provider and rules."""

    def __init__(self, populate: PopulateVehicle) -> None:
        self._populate = populate

    async def execute(
        self,
        *,
        tenant_id: UUID,
        vehicle_ids: list[UUID],
    ) -> BatchPopulateResult:
        unique_ids = list(dict.fromkeys(vehicle_ids))
        if not unique_ids:
            raise BatchValidationError("at least one vehicle_id is required")
        if len(unique_ids) > MAX_BATCH_SIZE:
            raise BatchValidationError(f"batch size cannot exceed {MAX_BATCH_SIZE}")
        items: list[BatchPopulateItem] = []
        for vehicle_id in unique_ids:
            items.append(await self._populate_one(tenant_id=tenant_id, vehicle_id=vehicle_id))
        return BatchPopulateResult(items=tuple(items))

    async def _populate_one(self, *, tenant_id: UUID, vehicle_id: UUID) -> BatchPopulateItem:
        try:
            vehicle = await self._populate.execute(tenant_id=tenant_id, vehicle_id=vehicle_id)
        except ApplicationError as error:
            return BatchPopulateItem(
                vehicle_id=vehicle_id,
                ok=False,
                vehicle=None,
                detail=str(error),
            )
        ok = vehicle.vehicle_status is VehicleStatus.READY_FOR_REVIEW
        return BatchPopulateItem(
            vehicle_id=vehicle_id,
            ok=ok,
            vehicle=vehicle,
            detail=None if ok else f"vehicle status is {vehicle.vehicle_status}",
        )
