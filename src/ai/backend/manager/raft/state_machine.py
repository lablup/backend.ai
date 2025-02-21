import asyncio
import pickle
from typing import Any, Optional, Self


class SetCommand:
    def __init__(self, key: str, value: str) -> None:
        self.key = key
        self.value = value

    def encode(self) -> bytes:
        return pickle.dumps(self.__dict__)

    @classmethod
    def decode(cls, packed: bytes) -> Self:
        unpacked = pickle.loads(packed)
        return cls(unpacked["key"], unpacked["value"])


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
        return pickle.dumps(self._store)

    async def restore(self, snapshot: bytes) -> None:
        self._store = pickle.loads(snapshot)
