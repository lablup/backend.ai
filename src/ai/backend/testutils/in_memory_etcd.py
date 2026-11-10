from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping
from types import TracebackType
from typing import Any, Literal

from ai.backend.common.etcd import make_dict_from_pairs

type EtcdOp = tuple[Literal["put", "delete"], str]


class _LockContext:
    _lock: asyncio.Lock

    def __init__(self, lock: asyncio.Lock) -> None:
        self._lock = lock

    async def __aenter__(self) -> _LockContext:
        await self._lock.acquire()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._lock.release()


class _NativeEtcd:
    """The `AsyncEtcd.etcd` client, reduced to the named lock."""

    _locks: dict[bytes, asyncio.Lock]

    def __init__(self) -> None:
        self._locks = {}

    def with_lock(self, option: Any) -> _LockContext:
        return _LockContext(self._locks.setdefault(option.lock_name, asyncio.Lock()))


class InMemoryEtcd:
    """`AsyncEtcd` over a dict, with its conditional writes and prefix reads; scopes are ignored.

    `ops` records every write that landed, in order; `deleted` the keys among them deleted.
    """

    store: dict[str, str]
    ops: list[EtcdOp]
    deleted: list[str]
    etcd: _NativeEtcd

    def __init__(self, store: Mapping[str, str] | None = None) -> None:
        self.store = dict(store or {})
        self.ops = []
        self.deleted = []
        self.etcd = _NativeEtcd()

    def _write(self, key: str, val: str) -> None:
        self.store[key] = val
        self.ops.append(("put", key))

    def _remove(self, key: str) -> None:
        self.store.pop(key, None)
        self.ops.append(("delete", key))
        self.deleted.append(key)

    def _holds(self, key: str, expected: str | None) -> bool:
        """None means absent."""
        return self.store.get(key) == expected

    async def open(self) -> None:
        pass

    async def close(self) -> None:
        pass

    async def get(self, key: str, **kwargs: Any) -> str | None:
        return self.store.get(key)

    async def get_prefix(self, prefix: str, **kwargs: Any) -> dict[str, Any]:
        pairs = sorted((k, v) for k, v in self.store.items() if k.startswith(prefix))
        return make_dict_from_pairs(prefix, pairs)

    async def iter_prefix(self, prefix: str, **kwargs: Any) -> AsyncIterator[tuple[str, str]]:
        for key in sorted(self.store):
            if key.startswith(prefix):
                yield key, self.store[key]

    async def put(self, key: str, val: str, **kwargs: Any) -> None:
        self._write(key, val)

    async def put_if_absent(self, key: str, val: str, **kwargs: Any) -> bool:
        if key in self.store:
            return False
        self._write(key, val)
        return True

    async def replace(self, key: str, initial_val: str, new_val: str, **kwargs: Any) -> bool:
        if not self._holds(key, initial_val):
            return False
        self._write(key, new_val)
        return True

    async def compare_and_put(
        self,
        key: str,
        val: str,
        *,
        expected: str | None,
        guards: Mapping[str, str | None],
        **kwargs: Any,
    ) -> bool:
        if not self._holds(key, expected) or not all(self._holds(k, v) for k, v in guards.items()):
            return False
        self._write(key, val)
        return True

    async def delete(self, key: str, **kwargs: Any) -> None:
        self._remove(key)

    async def delete_if_value(self, key: str, expected: str, **kwargs: Any) -> bool:
        if not self._holds(key, expected):
            return False
        self._remove(key)
        return True

    async def compare_and_delete(
        self,
        key: str,
        expected: str,
        *,
        guards: Mapping[str, str | None],
        **kwargs: Any,
    ) -> bool:
        if not self._holds(key, expected) or not all(self._holds(k, v) for k, v in guards.items()):
            return False
        self._remove(key)
        return True

    async def delete_prefix(self, prefix: str, **kwargs: Any) -> None:
        for key in [k for k in self.store if k.startswith(prefix)]:
            self._remove(key)

    async def watch_prefix(self, prefix: str, **kwargs: Any) -> AsyncIterator[None]:
        """No live events: the watch ends at once."""
        events: list[None] = []
        for event in events:
            yield event
