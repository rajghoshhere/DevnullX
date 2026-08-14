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


class SubmitVehicleRequest(BaseModel):
    registration_number: str | None = None
