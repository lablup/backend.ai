import abc
import uuid
from typing import Dict, Generic, Iterable, List, Optional, TypeVar, cast

import aioredis
import motor.motor_asyncio

from ...types import aobject
from .protos import raft_pb2

T = TypeVar('T')


class AbstractLogStorage(abc.ABC, Generic[T]):
    @abc.abstractmethod
    async def append_entries(self, entries: Iterable[T]) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def get(self, index: int) -> Optional[T]:
        raise NotImplementedError()

    @abc.abstractmethod
    async def clear(self, index: int) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def size(self) -> int:
        raise NotImplementedError()


class InMemoryLogStorage(aobject, Generic[T], AbstractLogStorage[T]):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._storage: List[T] = []

    async def __ainit__(self, *args, **kwargs) -> None:
        pass

    async def append_entries(self, entries: Iterable[T]) -> None:
        self._storage.extend(entries)

    async def get(self, index: int) -> Optional[T]:
        try:
            return self._storage[index]
        except IndexError:
            pass
        return None

    async def clear(self, index: int) -> None:
        assert hasattr(self._storage[0], 'index')
        self._storage = list(filter(lambda x: x.index < index, self._storage))  # type: ignore

    async def size(self) -> int:
        return len(self._storage)


class RedisLogStorage(aobject, Generic[T], AbstractLogStorage[T]):
    def __init__(self, *args, **kwargs) -> None:
        self._namespace: str = str(uuid.uuid4())

    async def __ainit__(self, *args, host: str = '127.0.0.1', port: int = 8111, **kwargs) -> None:
        keepalive_options: Dict[str, str] = {}
        self._redis = await aioredis.Redis.from_url(
            f'redis://{host}:{port}',
            socket_keepalive=True,
            socket_keepalive_options=keepalive_options,
        )

    async def append_entries(self, entries: Iterable[T]) -> None:
        if entries := tuple(entries):
            if isinstance(entries[0], (raft_pb2.Log,)):
                entries = map(lambda x: cast(x, raft_pb2.Log).SerializeToString(),  # type: ignore
                              filter(lambda x: x is not None, entries))             # type: ignore
            await self._redis.rpush(self._namespace, *entries)

    async def get(self, index: int) -> Optional[T]:
        if index >= 0:
            item = await self._redis.lindex(self._namespace, index)
        else:
            size = await self.size()
            item = await self._redis.lindex(self._namespace, size + index)

        if item is None:
            return None

        log = raft_pb2.Log()    # type: ignore
        log.ParseFromString(item)
        return log

    async def clear(self, index: int) -> None:
        pass

    async def size(self) -> int:
        return await self._redis.llen(self._namespace)


class MongoLogStorage(aobject, AbstractLogStorage[T]):
    def __init__(self, *args, **kwargs) -> None:
        username = kwargs.get('username', 'root')
        password = kwargs.get('password', '0000')
        host = kwargs.get('host', 'localhost')
        port = kwargs.get('port', 27017)

        self._uuid: str = str(uuid.uuid4()).split('-')[0]

        client = motor.motor_asyncio.AsyncIOMotorClient(f'mongodb://{username}:{password}@{host}:{port}')
        self._db = client['backend-ai']['raft'][self._uuid]

    async def __ainit__(self, *args, **kwargs) -> None:
        pass

    async def append_entries(self, entries: Iterable[T]) -> None:
        if entries := tuple(entries):
            if isinstance(entries[0], (raft_pb2.Log,)):
                entry_dicts = [
                    {
                        "index": entry.index,       # type: ignore
                        "term": entry.term,         # type: ignore
                        "command": entry.command,   # type: ignore
                    }
                    for entry in entries
                ]
                _ = await self._db.insert_many(entry_dicts)

    async def get(self, index: int) -> Optional[T]:
        return await self._db.find_one({"index": index})

    async def clear(self, index: int) -> None:
        await self._db.delete_many({"index": {"$le": index}})

    async def size(self) -> int:
        return await self._db.count_documents({})
