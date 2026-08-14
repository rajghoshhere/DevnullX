from __future__ import annotations

from typing import Protocol


class ObjectStorage(Protocol):
    async def put_bytes(self, key: str, data: bytes, content_type: str) -> str: ...

    async def get_bytes(self, key: str) -> bytes: ...
