from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from domain.tenant.entities import utc_now


@dataclass(frozen=True, slots=True)
class Manufacturer:
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def create(name: str) -> Manufacturer:
        stripped = name.strip()
        if not stripped:
            raise ValueError("manufacturer name is required")
        now = utc_now()
        return Manufacturer(id=uuid4(), name=stripped, created_at=now, updated_at=now)


@dataclass(frozen=True, slots=True)
class TruckModel:
    id: UUID
    manufacturer_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def create(*, manufacturer_id: UUID, name: str) -> TruckModel:
        stripped = name.strip()
        if not stripped:
            raise ValueError("truck model name is required")
        now = utc_now()
        return TruckModel(
            id=uuid4(),
            manufacturer_id=manufacturer_id,
            name=stripped,
            created_at=now,
            updated_at=now,
        )
