from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from domain.tenant.entities import utc_now


@dataclass(frozen=True, slots=True)
class FleetOwner:
    id: UUID
    tenant_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def create(*, tenant_id: UUID, name: str) -> FleetOwner:
        stripped = name.strip()
        if not stripped:
            raise ValueError("fleet owner name is required")
        now = utc_now()
        return FleetOwner(
            id=uuid4(),
            tenant_id=tenant_id,
            name=stripped,
            created_at=now,
            updated_at=now,
        )
