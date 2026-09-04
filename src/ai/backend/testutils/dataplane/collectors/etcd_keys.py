"""The cluster-wide control-plane state under ``network/``.

Unlike every other collector this one is not per-node — etcd is the shared source of truth, so its
resources carry an empty node name. It is also the collector that catches the failures nothing on
the host can show: a session block whose lease was never returned, a member record for an agent
that left, a VTEP key published by a node that has since been decommissioned.

Values are folded into the ident, not the detail, because a member record silently rewritten to
``vtep_ip: null`` is precisely the bug that took down healthy sessions once already. Identity by
key alone would have called that no change at all.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from ai.backend.testutils.dataplane.collectors.base import Resource

DEFAULT_PREFIXES: tuple[str, ...] = ("network/session/", "network/agent/")


class EtcdLike(Protocol):
    async def get_prefix(self, key_prefix: str) -> Mapping[str, Any]: ...


def flatten(prefix: str, tree: Mapping[str, Any]) -> dict[str, str]:
    """Flatten `AsyncEtcd.get_prefix`'s nested mapping back into absolute key -> value.

    `get_prefix` returns a directory-like tree and puts a node's own value under the empty-string
    key when that node is also a path prefix. Rebuilding the flat keys keeps the harness speaking
    the same vocabulary as `common/network/keys.py`, so a report can be pasted straight into
    `etcdctl`.
    """
    flat: dict[str, str] = {}

    def walk(path: str, node: Any) -> None:
        if isinstance(node, Mapping):
            for key, value in node.items():
                if key == "":
                    flat[path.rstrip("/")] = "" if value is None else str(value)
                else:
                    walk(f"{path}{key}/" if isinstance(value, Mapping) else f"{path}{key}", value)
        else:
            flat[path] = "" if node is None else str(node)

    walk(prefix, tree)
    return flat


class EtcdNetworkKeyCollector:
    _etcd: EtcdLike
    _prefixes: tuple[str, ...]

    def __init__(self, etcd: EtcdLike, *, prefixes: tuple[str, ...] = DEFAULT_PREFIXES) -> None:
        self._etcd = etcd
        self._prefixes = prefixes

    @property
    def kind(self) -> str:
        return "etcd"

    async def collect(self) -> set[Resource]:
        found: set[Resource] = set()
        for prefix in self._prefixes:
            tree = await self._etcd.get_prefix(prefix)
            for key, value in flatten(prefix, tree or {}).items():
                found.add(Resource(self.kind, "", f"{key}={value}"))
        return found
