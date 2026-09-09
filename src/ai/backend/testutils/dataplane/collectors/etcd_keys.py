"""The cluster-wide control-plane state under ``network/``.

Unlike every other collector this one is not per-node — etcd is the shared source of truth, so its
resources carry an empty node name. It is also the collector that catches the failures nothing on
the host can show: a session block whose lease was never returned, a member record for an agent
that left, a VTEP key published by a node that has since been decommissioned.

Values are folded into the ident, not the detail, because a member record silently rewritten to
``vtep_ip: null`` is precisely the bug that took down healthy sessions once already. Identity by
key alone would have called that no change at all.

The one field taken back out is ``updated_at``: it is the agent's heartbeat, so folding it in made
every snapshot differ from the one before it, and every scenario reported both agents' ``caps`` as
leaked *and* as collateral. The readiness digest excludes it for the same reason.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Final, Protocol

from ai.backend.testutils.dataplane.collectors.base import Resource

DEFAULT_PREFIXES: tuple[str, ...] = ("network/session/", "network/agent/")

#: Fields that say *when* a record was written or *which run of the agent* wrote it, rather than
#: what it holds. A record whose only difference is one of these is the same record.
_VOLATILE_FIELDS: Final = frozenset({"updated_at", "boot_id"})

#: Agent keys whose whole value IS the incarnation: the boot id, and the readiness digest that is
#: computed over it. A restart rotates both by design, so a scenario that restarts the agent would
#: otherwise report the node's own identity record as leaked *and* as collateral. The key's
#: presence is still compared -- an agent record that vanished, or appeared, is still a change.
_INCARNATION_KEYS: Final = frozenset({"boot", "ready"})


def stable_value(key: str, raw: str) -> str:
    """``raw`` without the parts that say *when* or *which run*, so an unchanged record compares
    equal to itself across a heartbeat and across an agent restart.

    A JSON object is rewritten with the volatile fields removed and its keys sorted (etcd stores
    the agent's serialization, whose key order is not guaranteed across versions). A key whose
    whole value is the incarnation keeps only its name. Everything else -- every other key under
    ``network/`` holds a bare scalar -- is returned untouched, so a member record rewritten to
    ``vtep_ip: null`` is still a different resource.
    """
    if key.rsplit("/", 1)[-1] in _INCARNATION_KEYS and key.startswith("network/agent/"):
        return "<incarnation>"
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return raw
    if not isinstance(parsed, dict):
        return raw
    return json.dumps(
        {k: v for k, v in parsed.items() if k not in _VOLATILE_FIELDS}, sort_keys=True
    )


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
                found.add(Resource(self.kind, "", f"{key}={stable_value(key, value)}"))
        return found
