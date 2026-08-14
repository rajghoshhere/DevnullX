from __future__ import annotations

from typing import Any, Protocol


class Queue(Protocol):
    async def publish(self, queue_name: str, message: dict[str, Any]) -> None: ...
