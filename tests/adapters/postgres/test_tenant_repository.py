from domain.tenant.entities import Tenant
from adapters.postgres.tenant_repository import PostgresTenantRepository


async def test_postgres_tenant_repository_round_trip(db_session) -> None:
    repository = PostgresTenantRepository(db_session)
    tenant = Tenant.create("Acme Logistics")

    saved = await repository.add(tenant)
    found = await repository.get_by_id(saved.id)

    assert found is not None
    assert found.id == tenant.id
    assert found.name == "Acme Logistics"
