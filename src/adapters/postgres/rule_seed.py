from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid5

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.postgres.models import RuleMasterModel
from domain.enrichment.models import Rule
from domain.tenant.entities import utc_now

RULES_DATA_PATH = Path(__file__).with_name("data") / "rules.json"
RULES_NAMESPACE = UUID("7a1c2e34-56b7-4d89-9e01-23456789abcd")


def rule_row_id(rule_id: str, version: str) -> UUID:
    return uuid5(RULES_NAMESPACE, f"{rule_id}:{version}")


def load_rule_seed_data() -> list[dict[str, object]]:
    return json.loads(RULES_DATA_PATH.read_text(encoding="utf-8"))


def builtin_rules(*, effective_from: datetime | None = None) -> list[Rule]:
    started = effective_from or datetime(2020, 1, 1, tzinfo=UTC)
    rules: list[Rule] = []
    for row in load_rule_seed_data():
        raw_expression = row["expression"]
        if not isinstance(raw_expression, dict):
            raise TypeError(f"expression for {row['rule_id']} must be an object")
        rules.append(
            Rule.create(
                rule_id=str(row["rule_id"]),
                name=str(row["name"]),
                version=str(row["version"]),
                rule_type=str(row["rule_type"]),
                expression=raw_expression,
                priority=int(row["priority"]),
                author=str(row.get("author") or "platform"),
                effective_from=started,
            )
        )
    return rules


async def seed_rules(session: AsyncSession) -> int:
    now = utc_now()
    effective_from = datetime(2020, 1, 1, tzinfo=UTC)
    upserted = 0
    for row in load_rule_seed_data():
        rule_id = str(row["rule_id"])
        version = str(row["version"])
        values = {
            "id": rule_row_id(rule_id, version),
            "rule_id": rule_id,
            "name": str(row["name"]),
            "version": version,
            "rule_type": str(row["rule_type"]),
            "expression": row["expression"],
            "priority": int(row["priority"]),
            "active": True,
            "effective_from": effective_from,
            "effective_to": None,
            "author": str(row.get("author") or "platform"),
            "created_at": now,
            "updated_at": now,
        }
        statement = insert(RuleMasterModel).values(**values)
        statement = statement.on_conflict_do_update(
            index_elements=["rule_id", "version"],
            set_={
                "name": statement.excluded.name,
                "rule_type": statement.excluded.rule_type,
                "expression": statement.excluded.expression,
                "priority": statement.excluded.priority,
                "active": statement.excluded.active,
                "effective_from": statement.excluded.effective_from,
                "effective_to": statement.excluded.effective_to,
                "author": statement.excluded.author,
                "updated_at": statement.excluded.updated_at,
            },
        )
        await session.execute(statement)
        upserted += 1
    await session.flush()
    return upserted
