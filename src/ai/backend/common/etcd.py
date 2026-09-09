"""
An asynchronous client wrapper for etcd v3 API.

It uses the etcd3 library using a thread pool executor.
We plan to migrate to aioetcd3 library but it requires more work to get maturity.
Fortunately, etcd3's watchers are not blocking because they are implemented
using callbacks in separate threads.
"""

from __future__ import annotations

import asyncio
import base64
import enum
import functools
import logging
from abc import ABC, abstractmethod
from collections import ChainMap, namedtuple
from collections.abc import (
    AsyncGenerator,
    Callable,
    Iterable,
    Mapping,
    MutableMapping,
    Sequence,
)
from types import TracebackType
from typing import (
    Any,
    ParamSpec,
    Self,
    TypeVar,
    cast,
    override,
)
from urllib.parse import quote as _quote
from urllib.parse import unquote

import aiohttp
import trafaret as t
from etcd_client import (
    Client as EtcdClient,
)
from etcd_client import (
    Communicator as EtcdCommunicator,
)
from etcd_client import (
    Compare,
    CompareOp,
    CondVar,
    ConnectOptions,
    GRPCStatusCode,
    GRPCStatusError,
    TxnOp,
    Watch,
)
from etcd_client import (
    Txn as EtcdTransactionAction,
)

from ai.backend.common.data.config.types import EtcdConfigData
from ai.backend.logging import BraceStyleAdapter

from .types import HostPortPair, QueueSentinel

__all__ = (
    "AsyncEtcd",
    "quote",
    "unquote",
)

Event = namedtuple("Event", "key event value")

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ConfigScopes(enum.Enum):
    MERGED = 0
    GLOBAL = 1
    SGROUP = 2
    NODE = 3


quote = functools.partial(_quote, safe="")


def make_dict_from_pairs(
    key_prefix: str, pairs: Iterable[tuple[str, str]], path_sep: str = "/"
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    len_prefix = len(key_prefix)
    if isinstance(pairs, dict):
        iterator: Iterable[tuple[str, str]] = pairs.items()
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


def _slash(v: str) -> str:
    return v.rstrip("/") + "/" if len(v) > 0 else ""


def _prefix_range_end(prefix: bytes) -> bytes:
    """Return etcd's exclusive range end for all keys beginning with ``prefix``."""
    end = bytearray(prefix)
    for index in range(len(end) - 1, -1, -1):
        if end[index] < 0xFF:
            end[index] += 1
            return bytes(end[: index + 1])
    return b"\0"


def _flatten_nested_dict(
    key_prefix: str,
    dict_obj: NestedStrKeyedMapping,
    out: dict[str, str] | None = None,
) -> dict[str, str]:
    """Flatten a nested dict into ``{slash-joined quoted key: value}`` pairs.

    An empty-string key maps to the parent prefix itself (value-at-prefix).
    """
    if out is None:
        out = {}
    for k, v in dict_obj.items():
        flattened_key = key_prefix if k == "" else key_prefix + "/" + quote(k)
        if isinstance(v, Mapping):
            _flatten_nested_dict(flattened_key, v, out)
        else:
            out[flattened_key] = v
    return out


P = ParamSpec("P")
R = TypeVar("R")

type GetPrefixValue = "Mapping[str, GetPrefixValue | str | None]"
type NestedStrKeyedMapping = "Mapping[str, str | NestedStrKeyedMapping]"
type NestedStrKeyedDict = "dict[str, str | NestedStrKeyedDict]"


class AbstractKVStore(ABC):
    """
    Abstract interface for Key-Value Store (KVS) operations
    Defines the basic operations that a KVS should support
    """

    @abstractmethod
    async def put(
        self,
        key: str,
        val: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> None:
        pass

    @abstractmethod
    async def put_prefix(
        self,
        key: str,
        dict_obj: NestedStrKeyedMapping,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> None:
        pass

    @abstractmethod
    async def put_dict(
        self,
        flattened_dict_obj: Mapping[str, str],
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> None:
        pass

    @abstractmethod
    async def get(
        self,
        key: str,
        *,
        scope: ConfigScopes = ConfigScopes.MERGED,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> str | None:
        pass

    @abstractmethod
    async def get_prefix(
        self,
        key_prefix: str,
        *,
        scope: ConfigScopes = ConfigScopes.MERGED,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> GetPrefixValue:
        pass

    @abstractmethod
    async def replace(
        self,
        key: str,
        initial_val: str,
        new_val: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> bool:
        pass

    @abstractmethod
    async def put_if_absent(
        self,
        key: str,
        val: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> bool:
        pass

    @abstractmethod
    async def compare_and_put(
        self,
        key: str,
        val: str,
        *,
        expected: str | None,
        guards: Mapping[str, str | None],
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> bool:
        pass

    @abstractmethod
    async def compare_and_delete(
        self,
        key: str,
        expected: str,
        *,
        guards: Mapping[str, str | None],
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> bool:
        pass

    @abstractmethod
    async def delete_if_value(
        self,
        key: str,
        expected: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> bool:
        pass

    @abstractmethod
    async def delete(
        self,
        key: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> None:
        pass

    @abstractmethod
    async def delete_multi(
        self,
        keys: Iterable[str],
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> None:
        pass

    @abstractmethod
    async def delete_prefix(
        self,
        key_prefix: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> None:
        pass

    @abstractmethod
    def watch(
        self,
        key: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
        once: bool = False,
        ready_event: CondVar | None = None,
        cleanup_event: CondVar | None = None,
        wait_timeout: float | None = None,
    ) -> AsyncGenerator[QueueSentinel | Event, None]:
        pass

    @abstractmethod
    def watch_prefix(
        self,
        key_prefix: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
        once: bool = False,
        ready_event: CondVar | None = None,
        cleanup_event: CondVar | None = None,
        wait_timeout: float | None = None,
    ) -> AsyncGenerator[QueueSentinel | Event, None]:
        pass


class AsyncEtcd(AbstractKVStore):
    etcd: EtcdClient
    _connect_options: ConnectOptions | None
    _credentials: dict[str, str] | None
    _http_endpoints: tuple[str, ...]

    def __init__(
        self,
        addrs: HostPortPair | Sequence[HostPortPair],
        namespace: str,
        scope_prefix_map: Mapping[ConfigScopes, str],
        *,
        credentials: dict[str, str] | None = None,
        encoding: str = "utf-8",
        watch_reconnect_intvl: float = 0.5,
        watch_reconnect_max_intvl: float = 30.0,
    ) -> None:
        self.scope_prefix_map = t.Dict({
            t.Key(ConfigScopes.GLOBAL): t.String(allow_blank=True),
            t.Key(ConfigScopes.SGROUP, optional=True): t.String,
            t.Key(ConfigScopes.NODE, optional=True): t.String,
        }).check(scope_prefix_map)

        if credentials is not None:
            self._connect_options = ConnectOptions().with_user(
                credentials["user"], credentials["password"]
            )
        else:
            self._connect_options = None

        self.ns = namespace
        if isinstance(addrs, HostPortPair):
            # Make it plural.
            addrs = [addrs]
        log.debug(
            'using etcd cluster at [{}] with namespace "{}"',
            ", ".join(str(addr) for addr in addrs),
            namespace,
        )
        self.encoding = encoding
        self.watch_reconnect_intvl = watch_reconnect_intvl
        self.watch_reconnect_max_intvl = watch_reconnect_max_intvl
        self._credentials = credentials
        self._http_endpoints = tuple(f"http://{addr.host}:{addr.port}" for addr in addrs)
        self.etcd = EtcdClient(
            list(self._http_endpoints),
            connect_options=self._connect_options,
        )

    def _calc_watch_reconnect_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay for watch reconnection.

        Args:
            attempt: 1-indexed retry count.

        Returns:
            Delay in seconds, capped at ``watch_reconnect_max_intvl``.
        """
        delay = self.watch_reconnect_intvl * (2 ** (attempt - 1))
        return cast(float, min(delay, self.watch_reconnect_max_intvl))

    @classmethod
    def create_from_config(cls, etcd_config: EtcdConfigData) -> Self:
        etcd_addrs = [addr.to_legacy() for addr in etcd_config.addrs]
        namespace = etcd_config.namespace
        etcd_user = etcd_config.user
        etcd_password = etcd_config.password

        credentials = None
        if etcd_user:
            if etcd_password is None:
                raise RuntimeError("etcd user is set, but password is not set")

            credentials = {
                "user": etcd_user,
                "password": etcd_password,
            }
        scope_prefix_map = {
            ConfigScopes.GLOBAL: "",
            # TODO: provide a way to specify other scope prefixes
        }

        return cls(etcd_addrs, namespace, scope_prefix_map, credentials=credentials)

    async def open(self) -> None:
        await self.etcd.__aenter__()

    async def close(self) -> None:
        await self.etcd.__aexit__(None, None, None)

    async def __aenter__(self) -> Self:
        await self.etcd.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        return cast(bool | None, await self.etcd.__aexit__(exc_type, exc_val, exc_tb))

    async def ping(self) -> None:
        """
        Ping the etcd server to check if the connection is alive.

        Raises:
            Exception: If the ping fails or connection is not available
        """
        # Attempt a simple get operation to test the connection
        # Even if the key doesn't exist, a successful query means the connection works
        # Connection errors will raise exceptions
        await self.get("_")

    def _mangle_key(self, k: str) -> str:
        k = k.removeprefix("/")
        return f"/sorna/{self.ns}/{k}"

    def _demangle_key(self, k: bytes | str) -> str:
        if isinstance(k, bytes):
            k = k.decode(self.encoding)
        prefix = f"/sorna/{self.ns}/"
        return k.removeprefix(prefix)

    def _merge_scope_prefix_map(
        self,
        override: Mapping[ConfigScopes, str] | None = None,
    ) -> Mapping[ConfigScopes, str]:
        """
        This stub ensures immutable usage of the ChainMap because ChainMap does *not*
        have the immutable version in typeshed.
        (ref: https://github.com/python/typeshed/issues/6042)
        """
        return ChainMap(cast(MutableMapping[str, Any], override) or {}, self.scope_prefix_map)

    @override
    async def put(
        self,
        key: str,
        val: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> None:
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
            await communicator.put(
                mangled_key.encode(self.encoding), str(val).encode(self.encoding)
            )

    @override
    async def put_prefix(
        self,
        key: str,
        dict_obj: NestedStrKeyedMapping,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> None:
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
        flattened_dict = _flatten_nested_dict(key, dict_obj)

        actions = []
        for k, v in flattened_dict.items():
            actions.append(
                TxnOp.put(
                    self._mangle_key(f"{_slash(scope_prefix)}{k}").encode(self.encoding),
                    str(v).encode(self.encoding),
                )
            )

        async with self.etcd.connect() as communicator:
            await communicator.txn(EtcdTransactionAction().and_then(actions).or_else([]))

    @override
    async def put_dict(
        self,
        flattened_dict_obj: Mapping[str, str],
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> None:
        """
        Put a flattened key-value pairs into the etcd.
        Since the given dict must be a flattened one, its keys must be quoted as needed by the caller.
        For new codes, ``put_prefix()`` is recommended.

        :param flattened_dict_obj: Flattened key-value pairs to put.
        :param scope: The config scope for putting the values.
        :param scope_prefix_map: The scope map used to mangle the prefix for the config scope.
        :return:
        """
        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]

        actions = []
        for k, v in flattened_dict_obj.items():
            actions.append(
                TxnOp.put(
                    self._mangle_key(f"{_slash(scope_prefix)}{k}").encode(self.encoding),
                    str(v).encode(self.encoding),
                )
            )

        async with self.etcd.connect() as communicator:
            await communicator.txn(EtcdTransactionAction().and_then(actions).or_else([]))

    async def atomic_replace_prefixes(
        self,
        replacements: Mapping[str, NestedStrKeyedMapping],
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> None:
        """Replace each subtree under the given prefixes in a single etcd transaction.

        For every ``(prefix, dict_obj)`` pair the subtree rooted at ``prefix`` is
        replaced by the flattened ``dict_obj``: keys present under the prefix but
        absent from the new contents are deleted, and every new key is put. The
        current-key reads and the delete/put operations are committed as one
        transaction so watchers (e.g. Traefik) never observe a partially-applied
        state where a router's backing service has briefly vanished.

        An empty ``dict_obj`` removes the whole subtree under its prefix. Prefixes
        are expected to be disjoint subtrees (one per logical object); sibling
        subtrees not listed in ``replacements`` are left untouched.

        :param replacements: Mapping of subtree prefix to its new nested contents.
            Both prefixes and dict keys must be quoted by the caller as needed.
        :param scope: The config scope for the operation.
        :param scope_prefix_map: The scope map used to mangle the prefix.
        """
        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]

        new_pairs: dict[str, str] = {}
        existing_keys: set[str] = set()
        async with self.etcd.connect() as communicator:
            for prefix, dict_obj in replacements.items():
                mangled_prefix = self._mangle_key(f"{_slash(scope_prefix)}{prefix}")
                pairs = await communicator.get_prefix(mangled_prefix.encode(self.encoding))
                for raw_key, _ in pairs:
                    existing_keys.add(bytes(raw_key).decode(self.encoding))
                for k, v in _flatten_nested_dict(prefix, dict_obj).items():
                    new_pairs[self._mangle_key(f"{_slash(scope_prefix)}{k}")] = str(v)

            stale_keys = existing_keys - new_pairs.keys()
            actions = [TxnOp.delete(k.encode(self.encoding)) for k in stale_keys]
            actions.extend(
                TxnOp.put(k.encode(self.encoding), v.encode(self.encoding))
                for k, v in new_pairs.items()
            )
            if not actions:
                return
            await communicator.txn(EtcdTransactionAction().and_then(actions).or_else([]))

    @override
    async def get(
        self,
        key: str,
        *,
        scope: ConfigScopes = ConfigScopes.MERGED,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> str | None:
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
                value = await communicator.get(
                    self._mangle_key(f"{_slash(scope_prefix)}{key}").encode(self.encoding)
                )
                if value is not None:
                    return bytes(value).decode(self.encoding)
        return None

    @override
    async def get_prefix(
        self,
        key_prefix: str,
        *,
        scope: ConfigScopes = ConfigScopes.MERGED,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
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
        pair_sets: list[list[tuple[str, str]]] = []
        async with self.etcd.connect() as communicator:
            for scope_prefix in scope_prefixes:
                mangled_key_prefix = self._mangle_key(f"{_slash(scope_prefix)}{key_prefix}")
                values = await communicator.get_prefix(mangled_key_prefix.encode(self.encoding))
                pair_sets.append([
                    (
                        self._demangle_key(bytes(k).decode(self.encoding)),
                        bytes(v).decode(self.encoding),
                    )
                    for k, v in values
                ])

        pair_sets = [sorted(pairs, key=lambda x: x[0]) for pairs in pair_sets]

        configs = [
            make_dict_from_pairs(f"{_slash(scope_prefix)}{key_prefix}", pairs, "/")
            for scope_prefix, pairs in zip(scope_prefixes, pair_sets, strict=True)
        ]
        return ChainMap(*configs)

    async def iter_prefix(
        self,
        key_prefix: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
        page_size: int = 256,
    ) -> AsyncGenerator[tuple[str, str], None]:
        """Stream one scope's prefix at a stable etcd revision in bounded pages."""
        if scope is ConfigScopes.MERGED:
            raise ValueError("iter_prefix requires one concrete etcd scope")
        if page_size < 1:
            raise ValueError("iter_prefix page_size must be positive")

        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]
        logical_scope_prefix = _slash(scope_prefix)
        mangled_prefix = self._mangle_key(f"{_slash(scope_prefix)}{key_prefix}").encode(
            self.encoding
        )
        range_end = _prefix_range_end(mangled_prefix)
        next_key = mangled_prefix
        revision: int | None = None
        headers: dict[str, dict[str, str]] = {}
        timeout = aiohttp.ClientTimeout(total=10.0)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            while True:
                payload: dict[str, str] = {
                    "key": base64.b64encode(next_key).decode("ascii"),
                    "range_end": base64.b64encode(range_end).decode("ascii"),
                    "limit": str(page_size),
                    "sort_order": "ASCEND",
                    "sort_target": "KEY",
                }
                if revision is not None:
                    payload["revision"] = str(revision)
                page = await self._request_range_page(session, payload, headers)
                if revision is None:
                    revision = int(page["header"]["revision"])
                kvs = page.get("kvs", [])
                if not kvs:
                    if page.get("more", False):
                        raise RuntimeError("etcd returned an empty range page with more=true")
                    return
                last_key: bytes | None = None
                for item in kvs:
                    raw_key = base64.b64decode(item["key"])
                    raw_value = base64.b64decode(item["value"])
                    last_key = raw_key
                    logical_key = self._demangle_key(raw_key).removeprefix(logical_scope_prefix)
                    yield logical_key, raw_value.decode(self.encoding)
                if not page.get("more", False):
                    return
                if last_key is None:
                    raise RuntimeError("etcd range page did not carry a continuation key")
                next_key = last_key + b"\0"

    async def _request_range_page(
        self,
        session: aiohttp.ClientSession,
        payload: Mapping[str, str],
        headers: dict[str, dict[str, str]],
    ) -> Mapping[str, Any]:
        """Read one range page, failing over across the configured cluster endpoints."""
        last_error: BaseException | None = None
        for endpoint in self._http_endpoints:
            try:
                for attempt in range(2):
                    endpoint_headers = headers.get(endpoint)
                    if endpoint_headers is None:
                        endpoint_headers = await self._range_auth_headers(session, endpoint)
                        headers[endpoint] = endpoint_headers
                    async with session.post(
                        f"{endpoint}/v3/kv/range",
                        json=payload,
                        headers=endpoint_headers,
                    ) as response:
                        if (
                            response.status == 401
                            and self._credentials is not None
                            and attempt == 0
                        ):
                            headers.pop(endpoint, None)
                            continue
                        response.raise_for_status()
                        result = await response.json()
                        if not isinstance(result, Mapping):
                            raise RuntimeError("etcd range response is not a JSON object")
                        return result
            except (aiohttp.ClientError, TimeoutError) as error:
                last_error = error
        if last_error is not None:
            raise last_error
        raise RuntimeError("no etcd endpoint is configured")

    async def _range_auth_headers(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
    ) -> dict[str, str]:
        """Authenticate the JSON range transport when etcd credentials are configured."""
        if self._credentials is None:
            return {}
        async with session.post(
            f"{endpoint}/v3/auth/authenticate",
            json={
                "name": self._credentials["user"],
                "password": self._credentials["password"],
            },
        ) as response:
            response.raise_for_status()
            result = await response.json()
        token = result.get("token") if isinstance(result, Mapping) else None
        if not isinstance(token, str) or not token:
            raise RuntimeError("etcd authentication returned no token")
        return {"Authorization": token}

    # for legacy
    get_prefix_dict = get_prefix

    @override
    async def replace(
        self,
        key: str,
        initial_val: str,
        new_val: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> bool:
        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]
        mangled_key = self._mangle_key(f"{_slash(scope_prefix)}{key}")

        async with self.etcd.connect() as communicator:
            result = await communicator.txn(
                EtcdTransactionAction()
                .when([
                    Compare.value(
                        mangled_key.encode(self.encoding),
                        CompareOp.EQUAL,
                        initial_val.encode(self.encoding),
                    ),
                ])
                .and_then([
                    TxnOp.put(mangled_key.encode(self.encoding), new_val.encode(self.encoding))
                ])
                .or_else([])
            )

            return cast(bool, result.succeeded())

    @override
    async def put_if_absent(
        self,
        key: str,
        val: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> bool:
        """
        Atomically put a single key-value pair only if the key does not already exist,
        using a compare-and-swap on ``create_revision == 0``.

        :return: ``True`` if this call created the key, ``False`` if it already existed.
        """
        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]
        mangled_key = self._mangle_key(f"{_slash(scope_prefix)}{key}")

        async with self.etcd.connect() as communicator:
            result = await communicator.txn(
                EtcdTransactionAction()
                .when([
                    Compare.create_revision(
                        mangled_key.encode(self.encoding),
                        CompareOp.EQUAL,
                        0,
                    ),
                ])
                .and_then([
                    TxnOp.put(mangled_key.encode(self.encoding), str(val).encode(self.encoding))
                ])
                .or_else([])
            )

            return cast(bool, result.succeeded())

    @override
    async def compare_and_put(
        self,
        key: str,
        val: str,
        *,
        expected: str | None,
        guards: Mapping[str, str | None],
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> bool:
        """
        Atomically write ``key`` only if it is in the expected state AND every guard key still
        holds exactly the bytes given for it -- or is still ABSENT, where the value given is
        ``None``. Absence is a condition like any other: a key that has appeared since the caller
        looked is a change, and often the one that matters.

        ``expected`` is the target's own condition: ``None`` means it must not exist yet,
        otherwise it must hold those exact bytes. ``guards`` are keys that are only READ --
        typically the record whose ownership makes this write legitimate at all.

        This is what a compare-and-swap on the target alone cannot express. A caller that checks
        it still owns a session and then writes the session's child key has two operations, and
        between them the session can be torn down and rebuilt: the child key it finds absent is
        absent because somebody else's cleanup removed it, and creating it there attaches this
        caller's state to a session that is not its. Naming the owning record as a guard makes the
        check and the write one thing, which the store either applies whole or does not apply.

        :return: ``True`` if the write landed, ``False`` if any condition failed.
        """
        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]
        mangled_key = self._mangle_key(f"{_slash(scope_prefix)}{key}")

        conditions = []
        if expected is None:
            conditions.append(
                Compare.create_revision(mangled_key.encode(self.encoding), CompareOp.EQUAL, 0)
            )
        else:
            conditions.append(
                Compare.value(
                    mangled_key.encode(self.encoding),
                    CompareOp.EQUAL,
                    expected.encode(self.encoding),
                )
            )
        for guard_key, guard_val in guards.items():
            mangled_guard = self._mangle_key(f"{_slash(scope_prefix)}{guard_key}")
            if guard_val is None:
                conditions.append(
                    Compare.create_revision(mangled_guard.encode(self.encoding), CompareOp.EQUAL, 0)
                )
            else:
                conditions.append(
                    Compare.value(
                        mangled_guard.encode(self.encoding),
                        CompareOp.EQUAL,
                        guard_val.encode(self.encoding),
                    )
                )

        async with self.etcd.connect() as communicator:
            result = await communicator.txn(
                EtcdTransactionAction()
                .when(conditions)
                .and_then([TxnOp.put(mangled_key.encode(self.encoding), val.encode(self.encoding))])
                .or_else([])
            )

            return cast(bool, result.succeeded())

    @override
    async def compare_and_delete(
        self,
        key: str,
        expected: str,
        *,
        guards: Mapping[str, str | None],
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> bool:
        """
        Atomically delete ``key`` only if it still holds ``expected`` AND every guard key is in
        the state given for it: those exact bytes, or -- for a guard value of ``None`` -- absent.

        The delete counterpart of :meth:`compare_and_put`, and needed for the same reason. A
        caller that decides a key is garbage by reading something ELSE, and then deletes the key,
        has made two operations out of one decision: between them the thing it read can change and
        the key can be released and taken by somebody to whom it is not garbage at all. Naming
        both in one transaction is what makes the decision and the delete the same event.

        :return: ``True`` if this call deleted the key, ``False`` if any condition failed.
        """
        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]
        mangled_key = self._mangle_key(f"{_slash(scope_prefix)}{key}")

        conditions = [
            Compare.value(
                mangled_key.encode(self.encoding),
                CompareOp.EQUAL,
                expected.encode(self.encoding),
            )
        ]
        for guard_key, guard_val in guards.items():
            mangled_guard = self._mangle_key(f"{_slash(scope_prefix)}{guard_key}")
            if guard_val is None:
                conditions.append(
                    Compare.create_revision(mangled_guard.encode(self.encoding), CompareOp.EQUAL, 0)
                )
            else:
                conditions.append(
                    Compare.value(
                        mangled_guard.encode(self.encoding),
                        CompareOp.EQUAL,
                        guard_val.encode(self.encoding),
                    )
                )

        async with self.etcd.connect() as communicator:
            result = await communicator.txn(
                EtcdTransactionAction()
                .when(conditions)
                .and_then([TxnOp.delete(mangled_key.encode(self.encoding))])
                .or_else([])
            )

            return cast(bool, result.succeeded())

    @override
    async def delete_if_value(
        self,
        key: str,
        expected: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> bool:
        """
        Atomically delete a single key only if it still holds ``expected``.

        The counterpart of :meth:`put_if_absent` for pooled resources: a plain delete releases
        whatever is there now, which after a reuse is somebody else's claim.

        :return: ``True`` if this call deleted the key, ``False`` if it held something else
                 (or nothing).
        """
        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]
        mangled_key = self._mangle_key(f"{_slash(scope_prefix)}{key}")

        async with self.etcd.connect() as communicator:
            result = await communicator.txn(
                EtcdTransactionAction()
                .when([
                    Compare.value(
                        mangled_key.encode(self.encoding),
                        CompareOp.EQUAL,
                        str(expected).encode(self.encoding),
                    ),
                ])
                .and_then([TxnOp.delete(mangled_key.encode(self.encoding))])
                .or_else([])
            )

            return cast(bool, result.succeeded())

    @override
    async def delete(
        self,
        key: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> None:
        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]
        mangled_key = self._mangle_key(f"{_slash(scope_prefix)}{key}")
        async with self.etcd.connect() as communicator:
            await communicator.delete(mangled_key.encode(self.encoding))

    @override
    async def delete_multi(
        self,
        keys: Iterable[str],
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> None:
        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]
        async with self.etcd.connect() as communicator:
            actions = []
            for k in keys:
                actions.append(
                    TxnOp.delete(
                        self._mangle_key(f"{_slash(scope_prefix)}{k}").encode(self.encoding)
                    )
                )
            await communicator.txn(EtcdTransactionAction().and_then(actions).or_else([]))

    @override
    async def delete_prefix(
        self,
        key_prefix: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> None:
        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]
        mangled_key_prefix = self._mangle_key(f"{_slash(scope_prefix)}{key_prefix}")
        async with self.etcd.connect() as communicator:
            await communicator.delete_prefix(mangled_key_prefix.encode(self.encoding))

    async def _watch_impl(
        self,
        iterator_factory: Callable[[EtcdCommunicator], Watch],
        scope_prefix_len: int,
        once: bool,
        cleanup_event: CondVar | None = None,
        wait_timeout: float | None = None,
    ) -> AsyncGenerator[QueueSentinel | Event, None]:
        try:
            async with self.etcd.connect() as communicator:
                iterator = iterator_factory(communicator)

                async for ev in iterator:
                    if wait_timeout is not None:
                        try:
                            ev = await asyncio.wait_for(iterator.__anext__(), wait_timeout)
                        except TimeoutError:
                            pass
                    yield Event(
                        bytes(ev.key).decode(self.encoding)[scope_prefix_len:],
                        ev.event,
                        bytes(ev.value).decode(self.encoding),
                    )
                    if once:
                        return
        finally:
            if cleanup_event:
                await cleanup_event.notify_waiters()

    @override
    async def watch(
        self,
        key: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
        once: bool = False,
        ready_event: CondVar | None = None,
        cleanup_event: CondVar | None = None,
        wait_timeout: float | None = None,
    ) -> AsyncGenerator[QueueSentinel | Event, None]:
        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]
        scope_prefix_len = len(self._mangle_key(f"{_slash(scope_prefix)}"))
        mangled_key = self._mangle_key(f"{_slash(scope_prefix)}{key}")
        retry_count: int = 0
        ended_without_error = False

        while not ended_without_error:
            try:
                async for ev in self._watch_impl(
                    lambda communicator: communicator.watch(
                        mangled_key.encode(self.encoding),
                        ready_event=ready_event,
                    ),
                    scope_prefix_len,
                    once,
                    cleanup_event=cleanup_event,
                    wait_timeout=wait_timeout,
                ):
                    if retry_count > 0:
                        log.info(
                            "watch(): successfully reconnected to Etcd server after %d retries",
                            retry_count,
                        )
                        retry_count = 0
                    yield ev
                ended_without_error = True
            except GRPCStatusError as e:
                err_detail = e.args[0]

                if err_detail["code"] == GRPCStatusCode.Unavailable:
                    retry_count += 1
                    delay = self._calc_watch_reconnect_delay(retry_count)
                    if retry_count == 1:
                        log.warning("watch(): error while connecting to Etcd server, retrying...")
                    else:
                        log.debug(
                            "watch(): still unable to connect to Etcd server (attempt %d),"
                            " next retry in %.1fs",
                            retry_count,
                            delay,
                        )
                    await asyncio.sleep(delay)
                    ended_without_error = False
                else:
                    raise

    @override
    async def watch_prefix(
        self,
        key_prefix: str,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
        once: bool = False,
        ready_event: CondVar | None = None,
        cleanup_event: CondVar | None = None,
        wait_timeout: float | None = None,
    ) -> AsyncGenerator[QueueSentinel | Event, None]:
        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]
        scope_prefix_len = len(self._mangle_key(f"{_slash(scope_prefix)}"))
        mangled_key_prefix = self._mangle_key(f"{_slash(scope_prefix)}{key_prefix}")
        retry_count: int = 0
        ended_without_error = False

        while not ended_without_error:
            try:
                async for ev in self._watch_impl(
                    lambda communicator: communicator.watch_prefix(
                        mangled_key_prefix.encode(self.encoding),
                        ready_event=ready_event,
                    ),
                    scope_prefix_len,
                    once,
                    cleanup_event=cleanup_event,
                    wait_timeout=wait_timeout,
                ):
                    if retry_count > 0:
                        log.info(
                            "watch_prefix(): successfully reconnected to Etcd server after %d retries",
                            retry_count,
                        )
                        retry_count = 0
                    yield ev
                ended_without_error = True
            except GRPCStatusError as e:
                err_detail = e.args[0]

                if err_detail["code"] == GRPCStatusCode.Unavailable:
                    retry_count += 1
                    delay = self._calc_watch_reconnect_delay(retry_count)
                    if retry_count == 1:
                        log.warning(
                            "watch_prefix(): error while connecting to Etcd server, retrying..."
                        )
                    else:
                        log.debug(
                            "watch_prefix(): still unable to connect to Etcd server (attempt %d),"
                            " next retry in %.1fs",
                            retry_count,
                            delay,
                        )
                    await asyncio.sleep(delay)
                    ended_without_error = False
                else:
                    raise
