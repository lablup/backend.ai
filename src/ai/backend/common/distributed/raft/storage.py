import abc
import sqlite3
import uuid
from pathlib import Path
from typing import Dict, Final, Iterable, List, Optional

import aioredis

from ...types import aobject
from .protos import raft_pb2


class AbstractLogStorage(abc.ABC):
    @abc.abstractmethod
    async def append_entries(self, entries: Iterable[raft_pb2.Log]) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def get(self, index: int) -> Optional[raft_pb2.Log]:
        raise NotImplementedError()

    @abc.abstractmethod
    async def last(self) -> Optional[raft_pb2.Log]:
        raise NotImplementedError()

    @abc.abstractmethod
    async def splice(self, index: int) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def size(self) -> int:
        raise NotImplementedError()


class InMemoryLogStorage(aobject, AbstractLogStorage):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._storage: List[raft_pb2.Log] = []

    async def __ainit__(self, *args, **kwargs) -> None:
        pass

    async def append_entries(self, entries: Iterable[raft_pb2.Log]) -> None:
        self._storage.extend(entries)

    async def get(self, index: int) -> Optional[raft_pb2.Log]:
        for log in self._storage:
            if log.index == index:
                return log
        return None

    async def last(self) -> Optional[raft_pb2.Log]:
        return self._storage[-1] if self._storage else None

    async def splice(self, index: int) -> None:
        self._storage = list(filter(lambda x: x.index < index, self._storage))

    async def size(self) -> int:
        return len(self._storage)


class SqliteLogStorage(aobject, AbstractLogStorage):
    def __init__(self, *args, **kwargs) -> None:
        self._id: str = kwargs.get("id") or str(uuid.uuid4())
        self._volatile: bool = kwargs.get("volatile", False)
        self._database = Path(__file__).parent / f"{self._id}.db"
        self._table: Final[str] = "raft"

        with sqlite3.connect(self.database) as conn:
            cur = conn.cursor()
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self._table}
                (idx INTEGER PRIMARY KEY, term INTEGER, command TEXT)
            """)
            conn.commit()

    def __del__(self):
        if self._volatile:
            with sqlite3.connect(self.database) as conn:
                cur = conn.cursor()
                cur.execute(f"DROP TABLE {self._table}")
                conn.commit()
            self._database.unlink(missing_ok=True)

    async def __ainit__(self, *args, **kwargs) -> None:
        pass

    async def append_entries(self, entries: Iterable[raft_pb2.Log]) -> None:
        entries = tuple((entry.index, entry.term, entry.command) for entry in entries)   # type: ignore
        with sqlite3.connect(self.database) as conn:
            cur = conn.cursor()
            cur.executemany(f"INSERT INTO {self._table} VALUES (?, ?, ?)", entries)   # type: ignore
            conn.commit()

    async def get(self, index: int) -> Optional[raft_pb2.Log]:
        with sqlite3.connect(self.database) as conn:
            cur = conn.cursor()
            if row := cur.execute(f"SELECT * FROM {self._table} WHERE idx = :index", {"index": index}).fetchone():
                row = raft_pb2.Log(index=row[0], term=row[1], command=row[2])
            return row

    async def last(self) -> Optional[raft_pb2.Log]:
        count = await self.size()
        with sqlite3.connect(self.database) as conn:
            cur = conn.cursor()
            if row := cur.execute(f"SELECT * FROM {self._table} LIMIT 1 OFFSET {count - 1}").fetchone():
                row = raft_pb2.Log(index=row[0], term=row[1], command=row[2])
            return row

    async def splice(self, index: int) -> None:
        with sqlite3.connect(self.database) as conn:
            cur = conn.cursor()
            cur.execute(f"DELETE FROM {self._table} WHERE idx >= :index", {"index": index})
            conn.commit()

    async def size(self) -> int:
        with sqlite3.connect(self.database) as conn:
            cur = conn.cursor()
            count, *_ = cur.execute(f"SELECT COUNT(*) FROM {self._table}").fetchone()
            return count

    @property
    def database(self) -> Path:
        return self._database


class RedisLogStorage(aobject, AbstractLogStorage):
    def __init__(self, *args, **kwargs) -> None:
        self._namespace: str = str(uuid.uuid4())

    async def __ainit__(self, *args, host: str = '127.0.0.1', port: int = 8111, **kwargs) -> None:
        keepalive_options: Dict[str, str] = {}
        self._redis = await aioredis.Redis.from_url(
            f'redis://{host}:{port}',
            socket_keepalive=True,
            socket_keepalive_options=keepalive_options,
        )

    async def append_entries(self, entries: Iterable[raft_pb2.Log]) -> None:
        if entries := tuple(entries):
            await self._redis.rpush(self._namespace, *entries)

    async def get(self, index: int) -> Optional[raft_pb2.Log]:
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

    async def last(self) -> Optional[raft_pb2.Log]:
        raise NotImplementedError()

    async def splice(self, index: int) -> None:
        pass

    async def size(self) -> int:
        return await self._redis.llen(self._namespace)
