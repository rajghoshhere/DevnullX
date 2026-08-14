from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AuthenticatedPrincipal:
    subject: str
    tenant_id: UUID | None
    roles: tuple[str, ...]


class AuthProvider(Protocol):
    async def authenticate(self, token: str) -> AuthenticatedPrincipal: ...
