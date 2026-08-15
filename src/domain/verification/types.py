from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(frozen=True, slots=True)
class VerificationContext:
    tenant_id: UUID
    vehicle_id: UUID
    correlation_id: str
    registration_number: str


@dataclass(frozen=True, slots=True)
class VerifiedVehicleAttributes:
    """Canonical RC fields. Provider-specific names never appear here."""

    registration_date: date | None = None
    manufacturing_month_year: date | None = None
    gvw_kg: int | None = None
    unladen_weight_kg: int | None = None
    engine_cc: int | None = None
    cylinder_count: int | None = None
    fuel_type: str | None = None
    body_type: str | None = None


@dataclass(frozen=True, slots=True)
class VehicleVerificationResult:
    success: bool
    provider: str
    correlation_id: str
    raw_object_key: str | None = None
    error_code: str | None = None
    attributes: VerifiedVehicleAttributes | None = None
