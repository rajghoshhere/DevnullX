from uuid import UUID

from fastapi import APIRouter, Depends, status

from api.dependencies import (
    PopulateBatchUseCase,
    PopulateVehicleUseCase,
    ProvenanceStore,
    ReviewVehicleUseCase,
    TenantId,
    get_create_fleet,
    get_create_fleet_owner,
    get_create_tenant,
    get_create_vehicle,
    get_fleet_owner,
    get_fleet_query,
    get_vehicle_query,
)
from api.schemas.onboarding import (
    BatchVerifyItemResponse,
    BatchVerifyRequest,
    BatchVerifyResponse,
    FleetOwnerResponse,
    FleetResponse,
    NamedCreateRequest,
    ReviewVehicleRequest,
    SubmitVehicleRequest,
    TenantCreateRequest,
    TenantResponse,
    VehicleCreateRequest,
    VehicleResponse,
    vehicle_to_response,
)
from application.commands.create_fleet import CreateFleet
from application.commands.create_fleet_owner import CreateFleetOwner
from application.commands.create_tenant import CreateTenant
from application.commands.create_vehicle import CreateVehicle
from application.queries.get_onboarding import GetFleet, GetFleetOwner, GetVehicle
from domain.vehicle.entities import Vehicle
from ports.repositories import ProvenanceRepository

router = APIRouter(prefix="/v1")


async def _vehicle_payload(vehicle: Vehicle, provenance: ProvenanceRepository) -> VehicleResponse:
    rows = await provenance.list_for_vehicle(vehicle.id)
    derived = {row.attribute: row.value for row in rows}
    return vehicle_to_response(vehicle, derived)


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
    return vehicle_to_response(vehicle)


@router.post("/vehicles/populate-batch", response_model=BatchVerifyResponse)
@router.post("/vehicles/verify-batch", response_model=BatchVerifyResponse, include_in_schema=False)
async def populate_vehicles_batch(
    payload: BatchVerifyRequest,
    tenant_id: TenantId,
    use_case: PopulateBatchUseCase,
    provenance: ProvenanceStore,
) -> BatchVerifyResponse:
    result = await use_case.execute(tenant_id=tenant_id, vehicle_ids=payload.vehicle_ids)
    items: list[BatchVerifyItemResponse] = []
    for item in result.items:
        vehicle_payload = None
        if item.vehicle is not None:
            vehicle_payload = await _vehicle_payload(item.vehicle, provenance)
        items.append(
            BatchVerifyItemResponse(
                vehicle_id=item.vehicle_id,
                ok=item.ok,
                detail=item.detail,
                vehicle=vehicle_payload,
            )
        )
    return BatchVerifyResponse(
        requested=result.requested,
        populated=result.populated,
        verified=result.populated,
        failed=result.failed,
        results=items,
    )


@router.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: UUID,
    tenant_id: TenantId,
    provenance: ProvenanceStore,
    use_case: GetVehicle = Depends(get_vehicle_query),
) -> VehicleResponse:
    vehicle = await use_case.execute(tenant_id=tenant_id, vehicle_id=vehicle_id)
    return await _vehicle_payload(vehicle, provenance)


@router.post("/vehicles/{vehicle_id}/populate", response_model=VehicleResponse)
@router.post(
    "/vehicles/{vehicle_id}/verify",
    response_model=VehicleResponse,
    include_in_schema=False,
)
async def populate_vehicle(
    vehicle_id: UUID,
    tenant_id: TenantId,
    use_case: PopulateVehicleUseCase,
    provenance: ProvenanceStore,
    payload: SubmitVehicleRequest | None = None,
) -> VehicleResponse:
    body = payload or SubmitVehicleRequest()
    vehicle = await use_case.execute(
        tenant_id=tenant_id,
        vehicle_id=vehicle_id,
        registration_number=body.registration_number,
    )
    return await _vehicle_payload(vehicle, provenance)


@router.post("/vehicles/{vehicle_id}/review", response_model=VehicleResponse)
async def review_vehicle(
    vehicle_id: UUID,
    tenant_id: TenantId,
    payload: ReviewVehicleRequest,
    use_case: ReviewVehicleUseCase,
    provenance: ProvenanceStore,
) -> VehicleResponse:
    vehicle = await use_case.execute(
        tenant_id=tenant_id,
        vehicle_id=vehicle_id,
        decision=payload.decision,
    )
    return await _vehicle_payload(vehicle, provenance)
