from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.postgres.taxonomy_models import TAXONOMY_MODELS
from domain.truck.taxonomy import TaxonomyTerm


class _TaxonomyRow(Protocol):
    id: UUID
    code: str
    name: str
    description: str | None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


def _to_domain(model: _TaxonomyRow) -> TaxonomyTerm:
    return TaxonomyTerm(
        id=model.id,
        code=model.code,
        name=model.name,
        description=model.description,
        sort_order=model.sort_order,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class PostgresTaxonomyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _model(self, table_name: str):
        try:
            return TAXONOMY_MODELS[table_name]
        except KeyError as error:
            raise ValueError(f"unknown taxonomy table: {table_name}") from error

    async def add(self, table_name: str, term: TaxonomyTerm) -> TaxonomyTerm:
        model = self._model(table_name)
        self._session.add(
            model(
                id=term.id,
                code=term.code,
                name=term.name,
                description=term.description,
                sort_order=term.sort_order,
                is_active=term.is_active,
                created_at=term.created_at,
                updated_at=term.updated_at,
            )
        )
        await self._session.flush()
        return term

    async def get_by_code(self, table_name: str, code: str) -> TaxonomyTerm | None:
        model = self._model(table_name)
        result = await self._session.execute(
            select(model).where(model.code == code.strip().upper())
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return _to_domain(row)

    async def get_by_id(self, table_name: str, term_id: UUID) -> TaxonomyTerm | None:
        model = self._model(table_name)
        result = await self._session.execute(select(model).where(model.id == term_id))
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return _to_domain(row)

    async def list_active(self, table_name: str) -> list[TaxonomyTerm]:
        model = self._model(table_name)
        result = await self._session.execute(
            select(model).where(model.is_active.is_(True)).order_by(model.sort_order, model.code)
        )
        return [_to_domain(row) for row in result.scalars().all()]
