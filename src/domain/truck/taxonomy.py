from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from domain.tenant.entities import utc_now


@dataclass(frozen=True, slots=True)
class TaxonomyTerm:
    id: UUID
    code: str
    name: str
    description: str | None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def create(
        *,
        code: str,
        name: str,
        description: str | None = None,
        sort_order: int = 0,
        is_active: bool = True,
        term_id: UUID | None = None,
    ) -> TaxonomyTerm:
        normalized_code = code.strip().upper()
        stripped_name = name.strip()
        if not normalized_code:
            raise ValueError("taxonomy code is required")
        if not stripped_name:
            raise ValueError("taxonomy name is required")
        now = utc_now()
        return TaxonomyTerm(
            id=term_id or uuid4(),
            code=normalized_code,
            name=stripped_name,
            description=description.strip() if description else None,
            sort_order=sort_order,
            is_active=is_active,
            created_at=now,
            updated_at=now,
        )
