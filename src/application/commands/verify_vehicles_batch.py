from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from application.commands.submit_vehicle_for_verification import SubmitVehicleForVerification
from application.errors import ApplicationError, BatchValidationError
from domain.vehicle.entities import Vehicle
from domain.vehicle.states import VehicleStatus

MAX_BATCH_SIZE = 100


@dataclass(frozen=True, slots=True)
class BatchVerificationItem:
    vehicle_id: UUID
    ok: bool
    vehicle: Vehicle | None
    detail: str | None


@dataclass(frozen=True, slots=True)
class BatchVerificationResult:
    items: tuple[BatchVerificationItem, ...]

    @property
    def requested(self) -> int:
        return len(self.items)

    @property
    def verified(self) -> int:
        return sum(
            1
            for item in self.items
            if item.vehicle is not None and item.vehicle.vehicle_status is VehicleStatus.VERIFIED
        )

    @property
    def failed(self) -> int:
        return sum(1 for item in self.items if not item.ok)


class VerifyVehiclesBatch:
    """Verify and populate many vehicles by id (bulk upload follow-up)."""

    def __init__(self, submit: SubmitVehicleForVerification) -> None:
        self._submit = submit

    async def execute(
        self,
        *,
        tenant_id: UUID,
        vehicle_ids: list[UUID],
    ) -> BatchVerificationResult:
        unique_ids = list(dict.fromkeys(vehicle_ids))
        if not unique_ids:
            raise BatchValidationError("at least one vehicle_id is required")
        if len(unique_ids) > MAX_BATCH_SIZE:
            raise BatchValidationError(f"batch size cannot exceed {MAX_BATCH_SIZE}")
        items: list[BatchVerificationItem] = []
        for vehicle_id in unique_ids:
            items.append(await self._verify_one(tenant_id=tenant_id, vehicle_id=vehicle_id))
        return BatchVerificationResult(items=tuple(items))

    async def _verify_one(self, *, tenant_id: UUID, vehicle_id: UUID) -> BatchVerificationItem:
        try:
            vehicle = await self._submit.execute(tenant_id=tenant_id, vehicle_id=vehicle_id)
        except ApplicationError as error:
            return BatchVerificationItem(
                vehicle_id=vehicle_id,
                ok=False,
                vehicle=None,
                detail=str(error),
            )
        ok = vehicle.vehicle_status is VehicleStatus.VERIFIED
        return BatchVerificationItem(
            vehicle_id=vehicle_id,
            ok=ok,
            vehicle=vehicle,
            detail=None if ok else f"vehicle status is {vehicle.vehicle_status}",
        )
