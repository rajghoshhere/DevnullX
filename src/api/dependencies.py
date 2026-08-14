from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.postgres.fleet_owner_repository import PostgresFleetOwnerRepository
from adapters.postgres.fleet_repository import PostgresFleetRepository
from adapters.postgres.session import get_db_session
from adapters.postgres.tenant_repository import PostgresTenantRepository
from adapters.postgres.vehicle_repository import PostgresVehicleRepository
from adapters.vehicle_providers.fake import FakeVehicleVerificationProvider
from application.commands.create_fleet import CreateFleet
from application.commands.create_fleet_owner import CreateFleetOwner
from application.commands.create_tenant import CreateTenant
from application.commands.create_vehicle import CreateVehicle
from application.commands.submit_vehicle_for_verification import SubmitVehicleForVerification
from application.queries.get_onboarding import GetFleet, GetFleetOwner, GetVehicle
from ports.repositories import (
    FleetOwnerRepository,
    FleetRepository,
    TenantRepository,
    VehicleRepository,
)
from ports.vehicle_provider import VehicleVerificationProvider

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
TenantId = Annotated[UUID, Header(alias="X-Tenant-ID")]


async def get_tenant_repository(session: DbSession) -> AsyncIterator[TenantRepository]:
    yield PostgresTenantRepository(session)


async def get_fleet_owner_repository(session: DbSession) -> AsyncIterator[FleetOwnerRepository]:
    yield PostgresFleetOwnerRepository(session)


async def get_fleet_repository(session: DbSession) -> AsyncIterator[FleetRepository]:
    yield PostgresFleetRepository(session)


async def get_vehicle_repository(session: DbSession) -> AsyncIterator[VehicleRepository]:
    yield PostgresVehicleRepository(session)


def get_verification_provider() -> VehicleVerificationProvider:
    return FakeVehicleVerificationProvider()


Tenants = Annotated[TenantRepository, Depends(get_tenant_repository)]
Owners = Annotated[FleetOwnerRepository, Depends(get_fleet_owner_repository)]
Fleets = Annotated[FleetRepository, Depends(get_fleet_repository)]
Vehicles = Annotated[VehicleRepository, Depends(get_vehicle_repository)]
VerificationProvider = Annotated[VehicleVerificationProvider, Depends(get_verification_provider)]


def get_create_tenant(tenants: Tenants) -> CreateTenant:
    return CreateTenant(tenants)


def get_create_fleet_owner(tenants: Tenants, owners: Owners) -> CreateFleetOwner:
    return CreateFleetOwner(tenants, owners)


def get_create_fleet(tenants: Tenants, fleets: Fleets) -> CreateFleet:
    return CreateFleet(tenants, fleets)


def get_create_vehicle(tenants: Tenants, fleets: Fleets, vehicles: Vehicles) -> CreateVehicle:
    return CreateVehicle(tenants, fleets, vehicles)


def get_submit_vehicle(
    vehicles: Vehicles, provider: VerificationProvider
) -> SubmitVehicleForVerification:
    return SubmitVehicleForVerification(vehicles, provider)


def get_fleet_owner(owners: Owners) -> GetFleetOwner:
    return GetFleetOwner(owners)


def get_fleet_query(fleets: Fleets) -> GetFleet:
    return GetFleet(fleets)


def get_vehicle_query(vehicles: Vehicles) -> GetVehicle:
    return GetVehicle(vehicles)


CreateTenantUseCase = Annotated[CreateTenant, Depends(get_create_tenant)]
CreateFleetOwnerUseCase = Annotated[CreateFleetOwner, Depends(get_create_fleet_owner)]
CreateFleetUseCase = Annotated[CreateFleet, Depends(get_create_fleet)]
CreateVehicleUseCase = Annotated[CreateVehicle, Depends(get_create_vehicle)]
SubmitVehicleUseCase = Annotated[SubmitVehicleForVerification, Depends(get_submit_vehicle)]
GetFleetOwnerUseCase = Annotated[GetFleetOwner, Depends(get_fleet_owner)]
GetFleetUseCase = Annotated[GetFleet, Depends(get_fleet_query)]
GetVehicleUseCase = Annotated[GetVehicle, Depends(get_vehicle_query)]
