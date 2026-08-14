from __future__ import annotations

from adapters.postgres.models import (
    FleetModel,
    FleetOwnerModel,
    ManufacturerModel,
    TenantModel,
    TruckModelRecord,
    VehicleModel,
)
from domain.fleet.entities import Fleet
from domain.owner.entities import FleetOwner
from domain.tenant.entities import Tenant
from domain.truck.entities import Manufacturer, TruckModel
from domain.vehicle.entities import Vehicle


def tenant_to_model(tenant: Tenant) -> TenantModel:
    return TenantModel(
        id=tenant.id,
        name=tenant.name,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


def tenant_to_domain(model: TenantModel) -> Tenant:
    return Tenant(
        id=model.id,
        name=model.name,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def fleet_owner_to_model(owner: FleetOwner) -> FleetOwnerModel:
    return FleetOwnerModel(
        id=owner.id,
        tenant_id=owner.tenant_id,
        name=owner.name,
        created_at=owner.created_at,
        updated_at=owner.updated_at,
    )


def fleet_owner_to_domain(model: FleetOwnerModel) -> FleetOwner:
    return FleetOwner(
        id=model.id,
        tenant_id=model.tenant_id,
        name=model.name,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def fleet_to_model(fleet: Fleet) -> FleetModel:
    return FleetModel(
        id=fleet.id,
        tenant_id=fleet.tenant_id,
        name=fleet.name,
        created_at=fleet.created_at,
        updated_at=fleet.updated_at,
    )


def fleet_to_domain(model: FleetModel) -> Fleet:
    return Fleet(
        id=model.id,
        tenant_id=model.tenant_id,
        name=model.name,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def manufacturer_to_model(manufacturer: Manufacturer) -> ManufacturerModel:
    return ManufacturerModel(
        id=manufacturer.id,
        name=manufacturer.name,
        created_at=manufacturer.created_at,
        updated_at=manufacturer.updated_at,
    )


def manufacturer_to_domain(model: ManufacturerModel) -> Manufacturer:
    return Manufacturer(
        id=model.id,
        name=model.name,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def truck_model_to_record(truck_model: TruckModel) -> TruckModelRecord:
    return TruckModelRecord(
        id=truck_model.id,
        manufacturer_id=truck_model.manufacturer_id,
        name=truck_model.name,
        created_at=truck_model.created_at,
        updated_at=truck_model.updated_at,
    )


def truck_model_to_domain(model: TruckModelRecord) -> TruckModel:
    return TruckModel(
        id=model.id,
        manufacturer_id=model.manufacturer_id,
        name=model.name,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def vehicle_to_model(vehicle: Vehicle) -> VehicleModel:
    return VehicleModel(
        id=vehicle.id,
        tenant_id=vehicle.tenant_id,
        fleet_id=vehicle.fleet_id,
        truck_model_id=vehicle.truck_model_id,
        registration_number=vehicle.registration_number,
        normalized_registration_number=vehicle.normalized_registration_number,
        registration_date=vehicle.registration_date,
        manufacturing_month_year=vehicle.manufacturing_month_year,
        gvw_kg=vehicle.gvw_kg,
        unladen_weight_kg=vehicle.unladen_weight_kg,
        engine_cc=vehicle.engine_cc,
        cylinder_count=vehicle.cylinder_count,
        fuel_type=vehicle.fuel_type,
        body_type=vehicle.body_type,
        vehicle_status=vehicle.vehicle_status,
        created_at=vehicle.created_at,
        updated_at=vehicle.updated_at,
    )


def vehicle_to_domain(model: VehicleModel) -> Vehicle:
    return Vehicle(
        id=model.id,
        tenant_id=model.tenant_id,
        fleet_id=model.fleet_id,
        truck_model_id=model.truck_model_id,
        registration_number=model.registration_number,
        normalized_registration_number=model.normalized_registration_number,
        registration_date=model.registration_date,
        manufacturing_month_year=model.manufacturing_month_year,
        gvw_kg=model.gvw_kg,
        unladen_weight_kg=model.unladen_weight_kg,
        engine_cc=model.engine_cc,
        cylinder_count=model.cylinder_count,
        fuel_type=model.fuel_type,
        body_type=model.body_type,
        vehicle_status=model.vehicle_status,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
