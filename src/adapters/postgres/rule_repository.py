from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.postgres.mappers import (
    provenance_to_domain,
    provenance_to_model,
    rule_to_domain,
    rule_to_model,
)
from adapters.postgres.models import RuleMasterModel, VehicleAttributeProvenanceModel
from domain.enrichment.models import Rule, VehicleAttributeProvenance


class PostgresRuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, rule: Rule) -> Rule:
        self._session.add(rule_to_model(rule))
        await self._session.flush()
        return rule

    async def list_effective(self, *, at: datetime) -> Sequence[Rule]:
        result = await self._session.execute(
            select(RuleMasterModel).where(RuleMasterModel.active.is_(True))
        )
        rules = [rule_to_domain(model) for model in result.scalars().all()]
        return [rule for rule in rules if rule.is_effective_at(at)]


class PostgresProvenanceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, row: VehicleAttributeProvenance) -> VehicleAttributeProvenance:
        self._session.add(provenance_to_model(row))
        await self._session.flush()
        return row

    async def list_for_vehicle(self, vehicle_id: UUID) -> Sequence[VehicleAttributeProvenance]:
        result = await self._session.execute(
            select(VehicleAttributeProvenanceModel)
            .where(VehicleAttributeProvenanceModel.vehicle_id == vehicle_id)
            .order_by(VehicleAttributeProvenanceModel.created_at)
        )
        return [provenance_to_domain(model) for model in result.scalars().all()]
