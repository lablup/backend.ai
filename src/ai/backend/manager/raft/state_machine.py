import asyncio
from typing import Any, Optional, Self


class SetCommand:
    def __init__(self, key: str, value: str) -> None:
        self.key = key
        self.value = value

    def encode(self) -> bytes:
        return f"{self.key}={self.value}".encode("utf-8")

    @classmethod
    def decode(cls, packed: bytes) -> Self:
        unpacked = packed.decode("utf-8").split("=", 1)
        if len(unpacked) != 2:
            raise ValueError("Invalid packed data")
        return cls(unpacked[0], unpacked[1])


class HashStore:
    def __init__(self) -> None:
        self._store: dict[str, Any] = {}
        self._loop = asyncio.get_running_loop()

    def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    def as_dict(self) -> dict:
        return self._store

    async def apply(self, msg: bytes) -> Optional[bytes]:
        message = SetCommand.decode(msg)
        self._store[message.key] = message.value
        return msg

    async def snapshot(self) -> bytes:
        return "\n".join(f"{k}={v}" for k, v in self._store.items()).encode("utf-8")

    async def restore(self, snapshot: bytes) -> None:
        self._store = dict(line.split("=", 1) for line in snapshot.decode("utf-8").split("\n"))
