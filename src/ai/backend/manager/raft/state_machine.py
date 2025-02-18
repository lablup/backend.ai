import asyncio
import pickle
from typing import Any, Optional


class RaftSetCommand:
    def __init__(self, key: str, value: str) -> None:
        self.key = key
        self.value = value

    def encode(self) -> bytes:
        return pickle.dumps(self.__dict__)

    @classmethod
    def decode(cls, packed: bytes) -> "RaftSetCommand":
        unpacked = pickle.loads(packed)
        return cls(unpacked["key"], unpacked["value"])


class RaftHashStore:
    def __init__(self) -> None:
        self._store: dict[str, Any] = {}
        self._loop = asyncio.get_running_loop()

    def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    def as_dict(self) -> dict:
        return self._store

    async def apply(self, msg: bytes) -> Optional[bytes]:
        message = RaftSetCommand.decode(msg)
        self._store[message.key] = message.value
        return msg

    async def snapshot(self) -> bytes:
        return pickle.dumps(self._store)

    async def restore(self, snapshot: bytes) -> None:
        self._store = pickle.loads(snapshot)
