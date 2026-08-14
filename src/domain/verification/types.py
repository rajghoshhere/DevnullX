from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class VerificationContext:
    tenant_id: UUID
    vehicle_id: UUID
    correlation_id: str
    registration_number: str


@dataclass(frozen=True, slots=True)
class VehicleVerificationResult:
    success: bool
    provider: str
    correlation_id: str
    raw_object_key: str | None = None
    error_code: str | None = None
