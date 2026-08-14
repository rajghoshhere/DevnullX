import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from adapters.postgres.manufacturer_repository import PostgresManufacturerRepository
from adapters.postgres.models import TruckModelRecord
from adapters.postgres.taxonomy_models import TAXONOMY_MODELS
from adapters.postgres.taxonomy_repository import PostgresTaxonomyRepository
from adapters.postgres.taxonomy_seed import load_taxonomy_seed_data, seed_taxonomy, taxonomy_id
from adapters.postgres.truck_model_repository import PostgresTruckModelRepository
from domain.truck.entities import Manufacturer, TruckModel
from domain.truck.taxonomy import TaxonomyTerm


async def test_seed_taxonomy_inserts_reference_codes(db_session) -> None:
    catalog = PostgresTaxonomyRepository(db_session)
    payload = load_taxonomy_seed_data()

    count = await seed_taxonomy(db_session)
    expected = sum(len(rows) for rows in payload.values())
    assert count == expected

    n3 = await catalog.get_by_code("regulatory_categories", "N3")
    assert n3 is not None
    assert n3.id == taxonomy_id("regulatory_categories", "N3")
    assert n3.name == "N3"
    assert "12 tonnes" in (n3.description or "")

    body_codes = {term.code for term in await catalog.list_active("body_types")}
    assert {"OPEN", "TIPPER", "TANKER", "SPECIAL_PURPOSE"} <= body_codes

    powertrains = {term.code for term in await catalog.list_active("powertrains")}
    assert {"DIESEL", "ELECTRIC", "HYDROGEN"} <= powertrains


async def test_seed_taxonomy_is_idempotent(db_session) -> None:
    first = await seed_taxonomy(db_session)
    second = await seed_taxonomy(db_session)
    assert first == second

    catalog = PostgresTaxonomyRepository(db_session)
    rows = await catalog.list_active("axle_configurations")
    assert [term.code for term in rows] == ["4X2", "6X2", "6X4", "8X2", "8X4"]


async def test_taxonomy_code_is_unique(db_session) -> None:
    catalog = PostgresTaxonomyRepository(db_session)
    await catalog.add(
        "body_types",
        TaxonomyTerm.create(code="CURTAIN_SIDER", name="Curtain sider"),
    )
    await db_session.flush()

    with pytest.raises(IntegrityError):
        async with db_session.begin_nested():
            await catalog.add(
                "body_types",
                TaxonomyTerm.create(code="CURTAIN_SIDER", name="Curtain-sider"),
            )
            await db_session.flush()


async def test_truck_model_can_reference_taxonomy_terms(db_session) -> None:
    await seed_taxonomy(db_session)
    catalog = PostgresTaxonomyRepository(db_session)
    manufacturer = Manufacturer.create("Ashok Leyland")
    await PostgresManufacturerRepository(db_session).add(manufacturer)

    n3 = await catalog.get_by_code("regulatory_categories", "N3")
    hcv = await catalog.get_by_code("truck_segments", "HCV")
    rigid = await catalog.get_by_code("truck_configurations", "RIGID")
    open_body = await catalog.get_by_code("body_types", "OPEN")
    axle = await catalog.get_by_code("axle_configurations", "8X4")
    diesel = await catalog.get_by_code("powertrains", "DIESEL")
    haulage = await catalog.get_by_code("truck_applications", "HAULAGE")
    assert n3 and hcv and rigid and open_body and axle and diesel and haulage

    truck_model = TruckModel.create(
        manufacturer_id=manufacturer.id,
        name="4021",
        regulatory_category_id=n3.id,
        truck_segment_id=hcv.id,
        truck_configuration_id=rigid.id,
        body_type_id=open_body.id,
        axle_configuration_id=axle.id,
        powertrain_id=diesel.id,
        truck_application_id=haulage.id,
    )
    await PostgresTruckModelRepository(db_session).add(truck_model)
    await db_session.flush()

    loaded = (
        await db_session.execute(
            select(TruckModelRecord)
            .options(
                selectinload(TruckModelRecord.regulatory_category),
                selectinload(TruckModelRecord.truck_segment),
                selectinload(TruckModelRecord.body_type),
                selectinload(TruckModelRecord.axle_configuration),
                selectinload(TruckModelRecord.powertrain),
            )
            .where(TruckModelRecord.id == truck_model.id)
        )
    ).scalar_one()

    assert loaded.regulatory_category.code == "N3"
    assert loaded.truck_segment.code == "HCV"
    assert loaded.body_type.code == "OPEN"
    assert loaded.axle_configuration.code == "8X4"
    assert loaded.powertrain.code == "DIESEL"


async def test_new_taxonomy_value_does_not_require_code_changes(db_session) -> None:
    catalog = PostgresTaxonomyRepository(db_session)
    extra = TaxonomyTerm.create(code="10X4", name="10x4", description="Five axles, two driven.")
    await catalog.add("axle_configurations", extra)
    await db_session.flush()

    found = await catalog.get_by_code("axle_configurations", "10x4")
    assert found is not None
    assert found.code == "10X4"
    assert "10X4" not in {row["code"] for row in load_taxonomy_seed_data()["axle_configurations"]}
    assert set(TAXONOMY_MODELS) == {
        "regulatory_categories",
        "truck_segments",
        "truck_configurations",
        "body_types",
        "axle_configurations",
        "powertrains",
        "truck_applications",
    }
