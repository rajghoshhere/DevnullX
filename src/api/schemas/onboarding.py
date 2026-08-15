from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from domain.vehicle.states import VehicleStatus


class TenantCreateRequest(BaseModel):
    name: str = Field(min_length=1)


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


class NamedCreateRequest(BaseModel):
    name: str = Field(min_length=1)


class FleetOwnerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


class FleetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


class VehicleCreateRequest(BaseModel):
    fleet_id: UUID
    truck_model_id: UUID | None = None
    registration_number: str | None = None
    registration_date: date | None = None
    manufacturing_month_year: date | None = None
    gvw_kg: int | None = Field(default=None, ge=0)
    unladen_weight_kg: int | None = Field(default=None, ge=0)
    engine_cc: int | None = Field(default=None, ge=0)
    cylinder_count: int | None = Field(default=None, ge=0)
    fuel_type: str | None = None
    body_type: str | None = None


class VehicleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    fleet_id: UUID
    truck_model_id: UUID | None
    registration_number: str | None
    registration_date: date | None
    manufacturing_month_year: date | None
    gvw_kg: int | None
    unladen_weight_kg: int | None
    engine_cc: int | None
    cylinder_count: int | None
    fuel_type: str | None
    body_type: str | None
    vehicle_status: VehicleStatus
    created_at: datetime
    updated_at: datetime
    derived_attributes: dict[str, str] = Field(default_factory=dict)


class SubmitVehicleRequest(BaseModel):
    registration_number: str | None = None


class BatchVerifyRequest(BaseModel):
    vehicle_ids: list[UUID] = Field(min_length=1, max_length=100)


class BatchVerifyItemResponse(BaseModel):
    vehicle_id: UUID
    ok: bool
    detail: str | None = None
    vehicle: VehicleResponse | None = None


class BatchVerifyResponse(BaseModel):
    requested: int
    populated: int = 0
    verified: int = 0
    failed: int
    results: list[BatchVerifyItemResponse]


class ReviewVehicleRequest(BaseModel):
    decision: str = Field(min_length=1)


def vehicle_to_response(
    vehicle: object, derived_attributes: dict[str, str] | None = None
) -> VehicleResponse:
    payload = VehicleResponse.model_validate(vehicle)
    return payload.model_copy(update={"derived_attributes": derived_attributes or {}})
