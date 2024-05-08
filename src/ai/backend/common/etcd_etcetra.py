"""
An asynchronous client wrapper for etcd v3 API.

It uses the etcd3 library using a thread pool executor.
We plan to migrate to aioetcd3 library but it requires more work to get maturity.
Fortunately, etcd3's watchers are not blocking because they are implemented
using callbacks in separate threads.
"""

from __future__ import annotations

import asyncio
import functools
import logging
from collections import ChainMap, namedtuple
from typing import (
    AsyncGenerator,
    AsyncIterator,
    Callable,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Optional,
    ParamSpec,
    Tuple,
    TypeAlias,
    TypeVar,
    Union,
    cast,
)
from urllib.parse import quote as _quote
from urllib.parse import unquote

import grpc  # pants: no-infer-dep (etcetra)
import trafaret as t
from etcetra import EtcdCommunicator, WatchEvent
from etcetra.client import EtcdClient, EtcdTransactionAction
from etcetra.types import CompareKey, EtcdCredential
from etcetra.types import HostPortPair as EtcetraHostPortPair

from .etcd import ConfigScopes
from .logging_utils import BraceStyleAdapter
from .types import HostPortPair, QueueSentinel

__all__ = (
    "quote",
    "unquote",
    "AsyncEtcd",
)

Event = namedtuple("Event", "key event value")

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


quote = functools.partial(_quote, safe="")


def make_dict_from_pairs(key_prefix, pairs, path_sep="/"):
    result = {}
    len_prefix = len(key_prefix)
    if isinstance(pairs, dict):
        iterator = pairs.items()
    else:
        iterator = pairs
    for k, v in iterator:
        if not k.startswith(key_prefix):
            continue
        subkey = k[len_prefix:]
        if subkey.startswith(path_sep):
            subkey = subkey[1:]
        path_components = subkey.split("/")
        parent = result
        for p in path_components[:-1]:
            p = unquote(p)
            if p not in parent:
                parent[p] = {}
            if p in parent and not isinstance(parent[p], dict):
                root = parent[p]
                parent[p] = {"": root}
            parent = parent[p]
        parent[unquote(path_components[-1])] = v
    return result


def _slash(v: str):
    return v.rstrip("/") + "/" if len(v) > 0 else ""


P = ParamSpec("P")
R = TypeVar("R")

GetPrefixValue: TypeAlias = "Mapping[str, GetPrefixValue | Optional[str]]"
NestedStrKeyedMapping: TypeAlias = "Mapping[str, str | NestedStrKeyedMapping]"
NestedStrKeyedDict: TypeAlias = "dict[str, str | NestedStrKeyedDict]"


class AsyncEtcd:
    etcd: EtcdClient

    _creds: Optional[EtcdCredential]

    def __init__(
        self,
        addr: HostPortPair | EtcetraHostPortPair,
        namespace: str,
        scope_prefix_map: Mapping[ConfigScopes, str],
        *,
        credentials: dict[str, str] | None = None,
        encoding: str = "utf-8",
        watch_reconnect_intvl: float = 0.5,
    ) -> None:
        self.scope_prefix_map = t.Dict({
            t.Key(ConfigScopes.GLOBAL): t.String(allow_blank=True),
            t.Key(ConfigScopes.SGROUP, optional=True): t.String,
            t.Key(ConfigScopes.NODE, optional=True): t.String,
        }).check(scope_prefix_map)
        if credentials is not None:
            self._creds = EtcdCredential(credentials["user"], credentials["password"])
        else:
            self._creds = None

        self.ns = namespace
        log.info('using etcd cluster from {} with namespace "{}"', addr, namespace)
        self.encoding = encoding
        self.watch_reconnect_intvl = watch_reconnect_intvl
        self.etcd = EtcdClient(
            EtcetraHostPortPair(str(addr.host), addr.port),
            credentials=self._creds,
            encoding=self.encoding,
        )

    async def close(self):
        pass  # for backward compatibility

    def _mangle_key(self, k: str) -> str:
        if k.startswith("/"):
            k = k[1:]
        return f"/sorna/{self.ns}/{k}"

    def _demangle_key(self, k: Union[bytes, str]) -> str:
        if isinstance(k, bytes):
            k = k.decode(self.encoding)
        prefix = f"/sorna/{self.ns}/"
        if k.startswith(prefix):
            k = k[len(prefix) :]
        return k

    def _merge_scope_prefix_map(
        self,
        override: Mapping[ConfigScopes, str] = None,
    ) -> Mapping[ConfigScopes, str]:
        """
        This stub ensures immutable usage of the ChainMap because ChainMap does *not*
        have the immutable version in typeshed.
        (ref: https://github.com/python/typeshed/issues/6042)
        """
        return ChainMap(cast(MutableMapping, override) or {}, self.scope_prefix_map)

    async def put(
        self,
        key: str,
        val: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] = None,
    ):
        """
        Put a single key-value pair to the etcd.

        :param key: The key. This must be quoted by the caller as needed.
        :param val: The value.
        :param scope: The config scope for putting the values.
        :param scope_prefix_map: The scope map used to mangle the prefix for the config scope.
        :return:
        """
        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]
        mangled_key = self._mangle_key(f"{_slash(scope_prefix)}{key}")
        async with self.etcd.connect() as communicator:
            await communicator.put(mangled_key, str(val))

    async def put_prefix(
        self,
        key: str,
        dict_obj: NestedStrKeyedMapping,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] = None,
    ):
        """
        Put a nested dict object under the given key prefix.
        All keys in the dict object are automatically quoted to avoid conflicts with the path separator.

        :param key: Prefix to put the given data. This must be quoted by the caller as needed.
        :param dict_obj: Nested dictionary representing the data.
        :param scope: The config scope for putting the values.
        :param scope_prefix_map: The scope map used to mangle the prefix for the config scope.
        :return:
        """
        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]
        flattened_dict: NestedStrKeyedDict = {}

        def _flatten(prefix: str, inner_dict: NestedStrKeyedDict) -> None:
            for k, v in inner_dict.items():
                if k == "":
                    flattened_key = prefix
                else:
                    flattened_key = prefix + "/" + quote(k)
                if isinstance(v, dict):
                    _flatten(flattened_key, v)
                else:
                    flattened_dict[flattened_key] = v

        _flatten(key, cast(NestedStrKeyedDict, dict_obj))

        def _txn(action: EtcdTransactionAction):
            for k, v in flattened_dict.items():
                action.put(self._mangle_key(f"{_slash(scope_prefix)}{k}"), str(v))

        async with self.etcd.connect() as communicator:
            await communicator.txn(_txn)

    async def put_dict(
        self,
        flattened_dict_obj: Mapping[str, str],
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] = None,
    ):
        """
        Put a flattened key-value pairs into the etcd.
        Since the given dict must be a flattened one, its keys must be quoted as needed by the caller.
        For new codes, ``put_prefix()`` is recommended.

        :param dict_obj: Flattened key-value pairs to put.
        :param scope: The config scope for putting the values.
        :param scope_prefix_map: The scope map used to mangle the prefix for the config scope.
        :return:
        """
        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]

        def _pipe(txn: EtcdTransactionAction):
            for k, v in flattened_dict_obj.items():
                txn.put(self._mangle_key(f"{_slash(scope_prefix)}{k}"), str(v))

        async with self.etcd.connect() as communicator:
            await communicator.txn(_pipe)

    async def get(
        self,
        key: str,
        *,
        scope: ConfigScopes = ConfigScopes.MERGED,
        scope_prefix_map: Mapping[ConfigScopes, str] = None,
    ) -> Optional[str]:
        """
        Get a single key from the etcd.
        Returns ``None`` if the key does not exist.
        The returned value may be an empty string if the value is a zero-length string.

        :param key: The key. This must be quoted by the caller as needed.
        :param scope: The config scope to get the value.
        :param scope_prefix_map: The scope map used to mangle the prefix for the config scope.
        :return:
        """

        _scope_prefix_map = self._merge_scope_prefix_map(scope_prefix_map)
        if scope == ConfigScopes.MERGED or scope == ConfigScopes.NODE:
            scope_prefixes = [_scope_prefix_map[ConfigScopes.GLOBAL]]
            p = _scope_prefix_map.get(ConfigScopes.SGROUP)
            if p is not None:
                scope_prefixes.insert(0, p)
            p = _scope_prefix_map.get(ConfigScopes.NODE)
            if p is not None:
                scope_prefixes.insert(0, p)
        elif scope == ConfigScopes.SGROUP:
            scope_prefixes = [_scope_prefix_map[ConfigScopes.GLOBAL]]
            p = _scope_prefix_map.get(ConfigScopes.SGROUP)
            if p is not None:
                scope_prefixes.insert(0, p)
        elif scope == ConfigScopes.GLOBAL:
            scope_prefixes = [_scope_prefix_map[ConfigScopes.GLOBAL]]
        else:
            raise ValueError("Invalid scope prefix value")

        async with self.etcd.connect() as communicator:
            for scope_prefix in scope_prefixes:
                value = await communicator.get(self._mangle_key(f"{_slash(scope_prefix)}{key}"))
                if value is not None:
                    return value
        return None

    async def get_prefix(
        self,
        key_prefix: str,
        *,
        scope: ConfigScopes = ConfigScopes.MERGED,
        scope_prefix_map: Mapping[ConfigScopes, str] = None,
    ) -> GetPrefixValue:
        """
        Retrieves all key-value pairs under the given key prefix as a nested dictionary.
        All dictionary keys are automatically unquoted.
        If a key has a value while it is also used as path prefix for other keys,
        the value directly referenced by the key itself is included as a value in a dictionary
        with the empty-string key.

        For instance, when the etcd database has the following key-value pairs:

        .. code-block::

           myprefix/mydata = abc
           myprefix/mydata/x = 1
           myprefix/mydata/y = 2
           myprefix/mykey = def

        ``get_prefix("myprefix")`` returns the following dictionary:

        .. code-block::

           {
             "mydata": {
               "": "abc",
               "x": "1",
               "y": "2",
             },
             "mykey": "def",
           }

        :param key_prefix: The key. This must be quoted by the caller as needed.
        :param scope: The config scope to get the value.
        :param scope_prefix_map: The scope map used to mangle the prefix for the config scope.
        :return:
        """

        _scope_prefix_map = self._merge_scope_prefix_map(scope_prefix_map)
        if scope == ConfigScopes.MERGED or scope == ConfigScopes.NODE:
            scope_prefixes = [_scope_prefix_map[ConfigScopes.GLOBAL]]
            p = _scope_prefix_map.get(ConfigScopes.SGROUP)
            if p is not None:
                scope_prefixes.insert(0, p)
            p = _scope_prefix_map.get(ConfigScopes.NODE)
            if p is not None:
                scope_prefixes.insert(0, p)
        elif scope == ConfigScopes.SGROUP:
            scope_prefixes = [_scope_prefix_map[ConfigScopes.GLOBAL]]
            p = _scope_prefix_map.get(ConfigScopes.SGROUP)
            if p is not None:
                scope_prefixes.insert(0, p)
        elif scope == ConfigScopes.GLOBAL:
            scope_prefixes = [_scope_prefix_map[ConfigScopes.GLOBAL]]
        else:
            raise ValueError("Invalid scope prefix value")
        pair_sets: List[List[Mapping | Tuple]] = []
        async with self.etcd.connect() as communicator:
            for scope_prefix in scope_prefixes:
                mangled_key_prefix = self._mangle_key(f"{_slash(scope_prefix)}{key_prefix}")
                values = await communicator.get_prefix(mangled_key_prefix)
                pair_sets.append([(self._demangle_key(k), v) for k, v in values.items()])

        configs = [
            make_dict_from_pairs(f"{_slash(scope_prefix)}{key_prefix}", pairs, "/")
            for scope_prefix, pairs in zip(scope_prefixes, pair_sets)
        ]
        return ChainMap(*configs)

    # for legacy
    get_prefix_dict = get_prefix

    async def replace(
        self,
        key: str,
        initial_val: str,
        new_val: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] = None,
    ) -> bool:
        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]
        mangled_key = self._mangle_key(f"{_slash(scope_prefix)}{key}")

        def _txn(success: EtcdTransactionAction, _):
            success.put(mangled_key, new_val)

        async with self.etcd.connect() as communicator:
            _, success = await communicator.txn_compare(
                [
                    CompareKey(mangled_key).value == initial_val,
                ],
                _txn,
            )
            return success

    async def delete(
        self,
        key: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] = None,
    ):
        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]
        mangled_key = self._mangle_key(f"{_slash(scope_prefix)}{key}")
        async with self.etcd.connect() as communicator:
            await communicator.delete(mangled_key)

    async def delete_multi(
        self,
        keys: Iterable[str],
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] = None,
    ):
        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]
        async with self.etcd.connect() as communicator:

            def _txn(action: EtcdTransactionAction):
                for k in keys:
                    action.delete(self._mangle_key(f"{_slash(scope_prefix)}{k}"))

            await communicator.txn(_txn)

    async def delete_prefix(
        self,
        key_prefix: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] = None,
    ):
        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]
        mangled_key_prefix = self._mangle_key(f"{_slash(scope_prefix)}{key_prefix}")
        async with self.etcd.connect() as communicator:
            await communicator.delete_prefix(mangled_key_prefix)

    async def _watch_impl(
        self,
        iterator_factory: Callable[[EtcdCommunicator], AsyncIterator[WatchEvent]],
        scope_prefix_len: int,
        once: bool,
        cleanup_event: Optional[asyncio.Event] = None,
        wait_timeout: Optional[float] = None,
    ) -> AsyncGenerator[Union[QueueSentinel, Event], None]:
        try:
            async with self.etcd.connect() as communicator:
                iterator = iterator_factory(communicator)
                async for ev in iterator:
                    if wait_timeout is not None:
                        try:
                            ev = await asyncio.wait_for(iterator.__anext__(), wait_timeout)
                        except asyncio.TimeoutError:
                            pass
                    yield Event(ev.key[scope_prefix_len:], ev.event, ev.value)
                    if once:
                        return
        finally:
            if cleanup_event:
                cleanup_event.set()

    async def watch(
        self,
        key: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] = None,
        once: bool = False,
        ready_event: asyncio.Event = None,
        cleanup_event: asyncio.Event = None,
        wait_timeout: float = None,
    ) -> AsyncGenerator[Union[QueueSentinel, Event], None]:
        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]
        scope_prefix_len = len(self._mangle_key(f"{_slash(scope_prefix)}"))
        mangled_key = self._mangle_key(f"{_slash(scope_prefix)}{key}")
        ended_without_error = False

        while not ended_without_error:
            try:
                async for ev in self._watch_impl(
                    lambda communicator: communicator.watch(
                        mangled_key,
                        ready_event=ready_event,
                    ),
                    scope_prefix_len,
                    once,
                    cleanup_event=cleanup_event,
                    wait_timeout=wait_timeout,
                ):
                    yield ev
                ended_without_error = True
            except grpc.aio.AioRpcError as e:
                if e.code() == grpc.StatusCode.UNAVAILABLE:
                    log.warning("watch(): error while connecting to Etcd server, retrying...")
                    await asyncio.sleep(self.watch_reconnect_intvl)
                    ended_without_error = False
                else:
                    raise

    async def watch_prefix(
        self,
        key_prefix: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] = None,
        once: bool = False,
        ready_event: asyncio.Event = None,
        cleanup_event: asyncio.Event = None,
        wait_timeout: float = None,
    ) -> AsyncGenerator[Union[QueueSentinel, Event], None]:
        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]
        scope_prefix_len = len(self._mangle_key(f"{_slash(scope_prefix)}"))
        mangled_key_prefix = self._mangle_key(f"{_slash(scope_prefix)}{key_prefix}")
        ended_without_error = False

        while not ended_without_error:
            try:
                async for ev in self._watch_impl(
                    lambda communicator: communicator.watch_prefix(
                        mangled_key_prefix,
                        ready_event=ready_event,
                    ),
                    scope_prefix_len,
                    once,
                    cleanup_event=cleanup_event,
                    wait_timeout=wait_timeout,
                ):
                    yield ev
                ended_without_error = True
            except grpc.aio.AioRpcError as e:
                if e.code() == grpc.StatusCode.UNAVAILABLE:
                    log.warning(
                        "watch_prefix(): error while connecting to Etcd server, retrying..."
                    )
                    await asyncio.sleep(self.watch_reconnect_intvl)
                    ended_without_error = False
                else:
                    raise e
