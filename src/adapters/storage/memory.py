from __future__ import annotations


class InMemoryObjectStorage:
    """Process-local ObjectStorage for tests and local development."""

    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}

    async def put_bytes(self, key: str, data: bytes, content_type: str) -> str:
        self.objects[key] = (data, content_type)
        return key

    async def get_bytes(self, key: str) -> bytes:
        try:
            return self.objects[key][0]
        except KeyError as error:
            raise FileNotFoundError(key) from error
