from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class Tenant:
    id: UUID
    name: str
    created_at: datetime

    @staticmethod
    def create(name: str) -> Tenant:
        stripped = name.strip()
        if not stripped:
            raise ValueError("tenant name is required")
        return Tenant(id=uuid4(), name=stripped, created_at=datetime.now(UTC))
