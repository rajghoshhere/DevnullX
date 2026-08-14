from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID, uuid5

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.postgres.taxonomy_models import TAXONOMY_MODELS
from domain.tenant.entities import utc_now

TAXONOMY_DATA_PATH = Path(__file__).with_name("data") / "taxonomy.json"
TAXONOMY_NAMESPACE = UUID("3d4f6a12-8c9e-4b71-9d02-a1b2c3d4e5f6")


def taxonomy_id(table_name: str, code: str) -> UUID:
    return uuid5(TAXONOMY_NAMESPACE, f"{table_name}:{code}")


def load_taxonomy_seed_data() -> dict[str, list[dict[str, object]]]:
    return json.loads(TAXONOMY_DATA_PATH.read_text(encoding="utf-8"))


async def seed_taxonomy(session: AsyncSession) -> int:
    payload = load_taxonomy_seed_data()
    now = utc_now()
    upserted = 0
    for table_name, rows in payload.items():
        model = TAXONOMY_MODELS[table_name]
        for row in rows:
            code = str(row["code"]).strip().upper()
            values = {
                "id": taxonomy_id(table_name, code),
                "code": code,
                "name": str(row["name"]).strip(),
                "description": str(row["description"]).strip() if row.get("description") else None,
                "sort_order": int(row.get("sort_order") or 0),
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }
            statement = insert(model).values(**values)
            statement = statement.on_conflict_do_update(
                index_elements=["code"],
                set_={
                    "name": statement.excluded.name,
                    "description": statement.excluded.description,
                    "sort_order": statement.excluded.sort_order,
                    "is_active": statement.excluded.is_active,
                    "updated_at": statement.excluded.updated_at,
                },
            )
            await session.execute(statement)
            upserted += 1
    await session.flush()
    return upserted
