from uuid import UUID

from fastapi import APIRouter, Depends, status

from application.commands.create_fleet import CreateFleet
from application.commands.create_fleet_owner import CreateFleetOwner
from application.commands.create_tenant import CreateTenant
from application.commands.create_vehicle import CreateVehicle
from application.commands.submit_vehicle_for_verification import SubmitVehicleForVerification
from application.queries.get_onboarding import GetFleet, GetFleetOwner, GetVehicle
from api.dependencies import (
    TenantId,
    get_create_fleet,
    get_create_fleet_owner,
    get_create_tenant,
    get_create_vehicle,
    get_fleet_owner,
    get_fleet_query,
    get_submit_vehicle,
    get_vehicle_query,
)
from api.schemas.onboarding import (
    FleetOwnerResponse,
    FleetResponse,
    NamedCreateRequest,
    SubmitVehicleRequest,
    TenantCreateRequest,
    TenantResponse,
    VehicleCreateRequest,
    VehicleResponse,
)

router = APIRouter(prefix="/v1")


@router.post("/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreateRequest,
    use_case: CreateTenant = Depends(get_create_tenant),
) -> TenantResponse:
    tenant = await use_case.execute(name=payload.name)
    return TenantResponse.model_validate(tenant)


@router.post("/owners", response_model=FleetOwnerResponse, status_code=status.HTTP_201_CREATED)
async def create_owner(
    payload: NamedCreateRequest,
    tenant_id: TenantId,
    use_case: CreateFleetOwner = Depends(get_create_fleet_owner),
) -> FleetOwnerResponse:
    owner = await use_case.execute(tenant_id=tenant_id, name=payload.name)
    return FleetOwnerResponse.model_validate(owner)


@router.get("/owners/{owner_id}", response_model=FleetOwnerResponse)
async def get_owner(
    owner_id: UUID,
    tenant_id: TenantId,
    use_case: GetFleetOwner = Depends(get_fleet_owner),
) -> FleetOwnerResponse:
    owner = await use_case.execute(tenant_id=tenant_id, owner_id=owner_id)
    return FleetOwnerResponse.model_validate(owner)


@router.post("/fleets", response_model=FleetResponse, status_code=status.HTTP_201_CREATED)
async def create_fleet(
    payload: NamedCreateRequest,
    tenant_id: TenantId,
    use_case: CreateFleet = Depends(get_create_fleet),
) -> FleetResponse:
    fleet = await use_case.execute(tenant_id=tenant_id, name=payload.name)
    return FleetResponse.model_validate(fleet)


@router.get("/fleets/{fleet_id}", response_model=FleetResponse)
async def get_fleet(
    fleet_id: UUID,
    tenant_id: TenantId,
    use_case: GetFleet = Depends(get_fleet_query),
) -> FleetResponse:
    fleet = await use_case.execute(tenant_id=tenant_id, fleet_id=fleet_id)
    return FleetResponse.model_validate(fleet)


@router.post("/vehicles", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    payload: VehicleCreateRequest,
    tenant_id: TenantId,
    use_case: CreateVehicle = Depends(get_create_vehicle),
) -> VehicleResponse:
    vehicle = await use_case.execute(tenant_id=tenant_id, **payload.model_dump())
    return VehicleResponse.model_validate(vehicle)


@router.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: UUID,
    tenant_id: TenantId,
    use_case: GetVehicle = Depends(get_vehicle_query),
) -> VehicleResponse:
    vehicle = await use_case.execute(tenant_id=tenant_id, vehicle_id=vehicle_id)
    return VehicleResponse.model_validate(vehicle)


@router.post("/vehicles/{vehicle_id}/verify", response_model=VehicleResponse)
async def submit_vehicle_for_verification(
    vehicle_id: UUID,
    tenant_id: TenantId,
    payload: SubmitVehicleRequest | None = None,
    use_case: SubmitVehicleForVerification = Depends(get_submit_vehicle),
) -> VehicleResponse:
    body = payload or SubmitVehicleRequest()
    vehicle = await use_case.execute(
        tenant_id=tenant_id,
        vehicle_id=vehicle_id,
        registration_number=body.registration_number,
    )
    return VehicleResponse.model_validate(vehicle)
