from collections.abc import Mapping
from typing import Any, cast
from urllib.parse import quote

from etcd_client import Txn as EtcdTransactionAction
from etcd_client import TxnOp

from ai.backend.common.etcd import AsyncEtcd, ConfigScopes, NestedStrKeyedMapping, _slash


class TraefikEtcd(AsyncEtcd):
    def _mangle_key(self, k: str) -> str:
        k = k.removeprefix("/")
        return f"{self.ns}/{k}"

    def _demangle_key(self, k: bytes | str) -> str:
        if isinstance(k, bytes):
            k = k.decode(self.encoding)
        prefix = f"{self.ns}/"
        return k.removeprefix(prefix)

    async def delete_prefixes(
        self,
        key_prefixes: list[str],
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> None:
        """Atomically delete every key under each of the given prefixes in a
        single etcd transaction.

        ``etcd_client``'s ``TxnOp`` does not expose ``DeleteRange`` directly,
        so this method first enumerates the concrete keys under each prefix
        via ``keys_prefix`` and then submits a single transaction containing
        one ``TxnOp.delete`` per enumerated key. The commit is atomic — if
        the transaction fails, no key is removed. Keys inserted after
        enumeration but before commit are not covered; callers should
        serialize writes to the affected prefixes (e.g. via a slot-level
        lock) so concurrent inserts cannot race this method.
        """
        if not key_prefixes:
            return
        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]
        async with self.etcd.connect() as communicator:
            keys_to_delete: list[bytes] = []
            for key_prefix in key_prefixes:
                mangled = self._mangle_key(f"{_slash(scope_prefix)}{key_prefix}")
                enumerated = await communicator.keys_prefix(mangled.encode(self.encoding))
                keys_to_delete.extend(enumerated)
            if not keys_to_delete:
                return
            actions = [TxnOp.delete(key) for key in keys_to_delete]
            await communicator.txn(EtcdTransactionAction().and_then(actions).or_else([]))

    async def replace_prefix(
        self,
        key_prefix: str,
        dict_obj: NestedStrKeyedMapping,
        *,
        scope: ConfigScopes = ConfigScopes.GLOBAL,
        scope_prefix_map: Mapping[ConfigScopes, str] | None = None,
    ) -> None:
        """Atomically replace the subtree under ``key_prefix`` with
        ``dict_obj`` via a single etcd transaction.

        Equivalent to ``delete_prefix(key_prefix)`` followed by
        ``put_prefix(key_prefix, dict_obj)`` but committed as one atomic
        txn — either the delete of stale leaves and the put of new leaves
        both commit, or neither does. This prevents the intermediate
        ``bai_service_{id}`` empty state that otherwise shows up when the
        put fails after the delete already landed.
        """
        scope_prefix = self._merge_scope_prefix_map(scope_prefix_map)[scope]
        flattened: dict[str, str] = {}

        def _flatten(prefix: str, inner: Any) -> None:
            if isinstance(inner, dict):
                for k, v in inner.items():
                    if k == "":
                        new_p = prefix
                    else:
                        new_p = prefix + "/" + quote(k)
                    _flatten(new_p, v)
            else:
                flattened[prefix] = str(inner)

        _flatten(key_prefix, cast(Any, dict_obj))

        async with self.etcd.connect() as communicator:
            mangled_prefix = self._mangle_key(f"{_slash(scope_prefix)}{key_prefix}")
            existing_keys = await communicator.keys_prefix(mangled_prefix.encode(self.encoding))

            actions: list[Any] = [TxnOp.delete(key) for key in existing_keys]
            for flat_key, value in flattened.items():
                mangled = self._mangle_key(f"{_slash(scope_prefix)}{flat_key}")
                actions.append(
                    TxnOp.put(
                        mangled.encode(self.encoding),
                        str(value).encode(self.encoding),
                    )
                )

            if not actions:
                return
            await communicator.txn(EtcdTransactionAction().and_then(actions).or_else([]))


def convert_to_etcd_dict(item: Any) -> dict[str, Any]:
    def _convert(obj: Any) -> Any:
        if isinstance(obj, list):
            return {str(idx): item for idx, item in enumerate(obj)}
        if isinstance(obj, dict):
            return {k: _convert(v) for k, v in obj.items()}
        return obj

    return cast(dict[str, Any], _convert(item))
