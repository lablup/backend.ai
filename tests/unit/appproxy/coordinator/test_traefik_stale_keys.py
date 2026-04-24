"""
Reproduction tests for the 2026-03-30 cross-model routing incident.

**Observed symptom** (incident report): Requests to model A's endpoint
returned responses alternately from model A and model B. "Route sync"
(which rewrites etcd from the DB source of truth) resolved the issue.

**Root mechanism** (hypothesized by the field report, pinned down here):

1. ``unload_traefik_circuit`` issues four sequential ``delete_prefix``
   calls — router, service, middleware 1, middleware 2 — against
   Traefik's etcd namespace. These four calls are *not* atomic: a
   transient failure after the first delete but before the remaining
   ones commits leaves etcd in a partial state where some of the
   circuit's Traefik metadata survives.

2. ``unload_circuits`` catches any ``Exception`` raised by
   ``unload_traefik_circuit``, logs it, and returns normally. The
   caller's DB transaction therefore commits the circuit deletion
   successfully — DB now has no record of the circuit, but etcd still
   holds the stale keys. This breaks the invariant that DB and etcd
   agree on which circuits exist.

3. When a later circuit B reuses the same frontend slot (port or
   subdomain), Traefik's etcd view contains both the new router and
   the stale one. The stale router's service URL points to a kernel
   host:port that has been reassigned to a different endpoint's
   kernel, and Traefik round-robins requests across the two
   apparently-healthy upstreams — producing the observed "alternating
   model A / model B response" symptom.

These tests pin down steps 1-2 deterministically with an in-memory
fake etcd that simulates a controlled ``delete_prefix`` failure, and
step 3 by publishing a second circuit on the same slot and inspecting
the resulting etcd key set.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.appproxy.common.types import ProxyProtocol
from ai.backend.appproxy.coordinator.models import Circuit
from ai.backend.appproxy.coordinator.types import CircuitManager

WORKER_AUTHORITY = "worker-1"
SLOT_PORT = 10640


@dataclass
class _FakeCircuit:
    """Minimal stand-in for a coordinator ``Circuit`` with the fields used
    by ``initialize_traefik_circuits`` and ``unload_traefik_circuit``."""

    id: UUID
    kernel_host: str
    kernel_port: int
    port: int = SLOT_PORT
    subdomain: str | None = None
    protocol: ProxyProtocol = ProxyProtocol.HTTP

    @property
    def worker_row(self) -> SimpleNamespace:
        return SimpleNamespace(authority=WORKER_AUTHORITY)

    @property
    def traefik_routers(self) -> dict[str, Any]:
        return {
            f"bai_router_{self.id}": {
                "rule": f"Host(`host-{WORKER_AUTHORITY}`)",
                "service": f"bai_service_{self.id}",
                "entrypoints": [f"portproxy_{self.port}"],
            }
        }

    @property
    def traefik_services(self) -> dict[str, Any]:
        return {
            f"bai_service_{self.id}": {
                "loadBalancer": {
                    "servers": [{"url": f"http://{self.kernel_host}:{self.kernel_port}/"}],
                },
            }
        }

    def get_traefik_middlewares(self, _local_config: object) -> dict[str, Any]:
        return {
            f"bai_appproxy_plugin_{self.id}": {"plugin": {"enabled": "true"}},
        }


@dataclass
class _FakeTraefikEtcd:
    """In-memory fake that tracks flat etcd keys and supports targeted
    failure injection on every write-path method.

    Counters are per-method so tests can target e.g. "fail on the first
    ``delete_prefixes`` call" without worrying about interleaved
    ``delete_prefix`` activity from other code paths.
    """

    keys: dict[str, str] = field(default_factory=dict)
    fail_on_delete_nth: int | None = None
    fail_on_delete_prefixes_nth: int | None = None
    fail_on_put_nth: int | None = None
    fail_on_replace_nth: int | None = None
    _delete_call_count: int = field(default=0, init=False)
    _delete_prefixes_call_count: int = field(default=0, init=False)
    _put_call_count: int = field(default=0, init=False)
    _replace_call_count: int = field(default=0, init=False)

    async def put_prefix(self, key: str, dict_obj: Any) -> None:
        self._put_call_count += 1
        if self.fail_on_put_nth == self._put_call_count:
            raise ConnectionError(f"simulated etcd blip on put #{self._put_call_count}: {key}")
        for flat_key, value in _flatten(key, dict_obj):
            self.keys[flat_key] = value

    async def delete_prefix(self, prefix: str) -> None:
        self._delete_call_count += 1
        if self.fail_on_delete_nth == self._delete_call_count:
            raise ConnectionError(
                f"simulated etcd blip on delete #{self._delete_call_count}: {prefix}"
            )
        for k in [k for k in list(self.keys) if k == prefix or k.startswith(prefix + "/")]:
            del self.keys[k]

    async def delete_prefixes(self, prefixes: list[str]) -> None:
        """Atomic multi-prefix delete (mirrors TraefikEtcd.delete_prefixes).

        The real implementation wraps the deletes in a single etcd txn, so
        the fake mirrors that: either every matching key is removed or the
        stored state is left untouched on failure.
        """
        self._delete_prefixes_call_count += 1
        if self.fail_on_delete_prefixes_nth == self._delete_prefixes_call_count:
            raise ConnectionError(
                f"simulated etcd blip on delete_prefixes "
                f"#{self._delete_prefixes_call_count}: {prefixes}"
            )
        for prefix in prefixes:
            for k in [k for k in list(self.keys) if k == prefix or k.startswith(prefix + "/")]:
                del self.keys[k]

    async def replace_prefix(self, prefix: str, dict_obj: Any) -> None:
        """Atomic delete-then-put under ``prefix`` (mirrors TraefikEtcd.replace_prefix).

        Either the subtree is fully replaced with ``dict_obj``'s leaves or
        the stored state is left unchanged on failure.
        """
        self._replace_call_count += 1
        if self.fail_on_replace_nth == self._replace_call_count:
            raise ConnectionError(
                f"simulated etcd blip on replace_prefix #{self._replace_call_count}: {prefix}"
            )
        for k in [k for k in list(self.keys) if k == prefix or k.startswith(prefix + "/")]:
            del self.keys[k]
        for flat_key, value in _flatten(prefix, dict_obj):
            self.keys[flat_key] = value

    async def get_prefix(self, prefix: str) -> dict[str, str]:
        return {k: v for k, v in self.keys.items() if k == prefix or k.startswith(prefix + "/")}

    def count_keys_for(self, circuit_id: UUID) -> int:
        """How many of this circuit's etcd keys currently remain.

        Matches the router / service / middleware key markers emitted by
        ``_FakeCircuit.traefik_*`` and ``get_traefik_middlewares``.
        """
        id_str = str(circuit_id)
        markers = (
            f"bai_router_{id_str}",
            f"bai_service_{id_str}",
            f"bai_appproxy_plugin_{id_str}",
        )
        return sum(1 for k in self.keys if any(m in k for m in markers))


def _flatten(prefix: str, obj: Any) -> list[tuple[str, str]]:
    """Flatten a nested dict into ``(flat_key, value)`` tuples, matching
    how ``AsyncEtcd.put_prefix`` writes leaves into etcd."""

    out: list[tuple[str, str]] = []

    def _rec(p: str, o: Any) -> None:
        if isinstance(o, dict):
            for k, v in o.items():
                new_p = p if k == "" else (p + "/" + k if p else k)
                _rec(new_p, v)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                new_p = p + "/" + str(i) if p else str(i)
                _rec(new_p, v)
        else:
            out.append((p, str(o)))

    _rec(prefix, obj)
    return out


@pytest.fixture
def fake_etcd() -> _FakeTraefikEtcd:
    return _FakeTraefikEtcd()


@pytest.fixture
def circuit_manager(fake_etcd: _FakeTraefikEtcd) -> CircuitManager:
    return CircuitManager(
        event_dispatcher=cast(Any, MagicMock()),
        event_producer=cast(Any, MagicMock()),
        traefik_etcd=cast(Any, fake_etcd),
        local_config=cast(
            Any,
            SimpleNamespace(
                proxy_coordinator=SimpleNamespace(enable_traefik=True),
            ),
        ),
    )


def _make_circuit(kernel_host: str, kernel_port: int) -> Circuit:
    return cast(
        Circuit,
        _FakeCircuit(
            id=uuid4(),
            kernel_host=kernel_host,
            kernel_port=kernel_port,
        ),
    )


class TestUnloadAbsorbsTransientFailure:
    """
    Before the fix, ``unload_traefik_circuit`` issued four sequential
    ``delete_prefix`` calls and ``unload_circuits`` silently swallowed
    any exception. The fix bundles the four deletes into a single
    atomic txn (``delete_prefixes``) and adds bounded retry + re-raise
    around it. The net invariant: ``unload_circuits`` only returns
    normally when etcd is clean for the unloaded circuit.
    """

    async def test_unload_succeeds_cleanly_despite_transient_failure(
        self,
        circuit_manager: CircuitManager,
        fake_etcd: _FakeTraefikEtcd,
    ) -> None:
        """
        The first atomic ``delete_prefixes`` call hits a transient etcd
        error; the retry loop inside ``unload_circuits`` re-attempts and
        succeeds. After the call returns, etcd must hold zero keys for
        the unloaded circuit.
        """
        circuit = _make_circuit(kernel_host="10.0.0.1", kernel_port=30000)
        await circuit_manager.initialize_traefik_circuits([circuit])
        seeded = fake_etcd.count_keys_for(circuit.id)
        assert seeded > 0, "precondition: circuit must seed etcd keys"

        # Fail only on the first atomic delete; the retry's second
        # attempt is call #2 and therefore not impacted.
        fake_etcd.fail_on_delete_prefixes_nth = 1

        await circuit_manager.unload_circuits([circuit])

        remaining = fake_etcd.count_keys_for(circuit.id)
        assert remaining == 0, (
            f"{remaining} of {seeded} etcd key(s) for circuit "
            f"{circuit.id} survived a unload call that returned without "
            "raising. A transient etcd blip must be absorbed by the "
            "retry loop — partial / stale state is not permitted."
        )

    async def test_unload_reraises_on_persistent_failure(
        self,
        circuit_manager: CircuitManager,
        fake_etcd: _FakeTraefikEtcd,
    ) -> None:
        """
        When every retry fails, ``unload_circuits`` must re-raise so the
        caller's DB transaction rolls back. Atomic delete ensures etcd
        state is unchanged on each failed attempt (all-or-nothing), so
        after the final raise, etcd still holds the circuit's keys —
        consistent with DB, which (because the caller will roll back)
        still holds the circuit row.
        """
        circuit = _make_circuit(kernel_host="10.0.0.1", kernel_port=30000)
        await circuit_manager.initialize_traefik_circuits([circuit])
        seeded = fake_etcd.count_keys_for(circuit.id)

        # Fail every retry attempt (max_attempts=3 by default).
        fake_etcd.fail_on_delete_prefixes_nth = 1

        class _AlwaysFail:
            def __init__(self, real_etcd: _FakeTraefikEtcd) -> None:
                self._etcd = real_etcd

            async def delete_prefixes(self, prefixes: list[str]) -> None:
                raise ConnectionError("persistent etcd failure")

            def __getattr__(self, name: str) -> Any:
                return getattr(self._etcd, name)

        circuit_manager.traefik_etcd = cast(Any, _AlwaysFail(fake_etcd))

        with pytest.raises(ConnectionError):
            await circuit_manager.unload_circuits([circuit])

        remaining = fake_etcd.count_keys_for(circuit.id)
        assert remaining == seeded, (
            f"atomic delete_prefixes failed persistently but etcd has "
            f"{remaining} of {seeded} keys — atomic txn should leave "
            "state untouched on failure (all-or-nothing)"
        )


class TestIncidentEndToEnd:
    """
    Full incident trace: unload A' (with a transient etcd failure
    during the delete step) → publish A on the same slot with a
    different kernel host:port. After the fix, even though the first
    unload attempt hits an error, the retry absorbs it, no stale keys
    persist, and the subsequent publish leaves exactly one router on
    the slot — the symptom observed on 2026-03-30 cannot form.
    """

    async def test_unload_then_publish_on_same_slot_produces_no_coexistence(
        self,
        circuit_manager: CircuitManager,
        fake_etcd: _FakeTraefikEtcd,
    ) -> None:
        circuit_a_prime = _make_circuit(kernel_host="10.0.0.1", kernel_port=30000)
        await circuit_manager.initialize_traefik_circuits([circuit_a_prime])

        # Transient unload failure on first attempt; retry (attempt #2
        # → delete_prefixes call #2) absorbs it.
        fake_etcd.fail_on_delete_prefixes_nth = 1
        await circuit_manager.unload_circuits([circuit_a_prime])
        assert fake_etcd.count_keys_for(circuit_a_prime.id) == 0, (
            "unload with transient failure must still end with etcd cleaned; "
            f"{fake_etcd.count_keys_for(circuit_a_prime.id)} stale keys remain"
        )

        circuit_a_new = _make_circuit(kernel_host="10.0.0.1", kernel_port=45123)
        await circuit_manager.initialize_traefik_circuits([circuit_a_new])

        routers_prefix = f"worker_{WORKER_AUTHORITY}/http/routers"
        router_keys = await fake_etcd.get_prefix(routers_prefix)
        distinct_router_ids: set[str] = set()
        for k in router_keys:
            parts = k.removeprefix(routers_prefix + "/").split("/", 1)
            if parts and parts[0].startswith("bai_router_"):
                distinct_router_ids.add(parts[0].removeprefix("bai_router_"))

        assert distinct_router_ids == {str(circuit_a_new.id)}, (
            f"two routers coexist on slot port={SLOT_PORT} in etcd: "
            f"{sorted(distinct_router_ids)}. With the unload fix, a "
            f"transient unload failure must not leak a stale router "
            f"into the slot — this is the 2026-03-30 incident's mechanism"
        )


class TestUpdatePartialLeavesEmptyService:
    """
    ``update_traefik_circuit_routes`` performs a ``delete_prefix`` +
    ``put_prefix`` sequence against ``{scope}/services/bai_service_{id}``
    — two independent etcd RPCs. If the put fails after the delete has
    already committed, etcd ends up with an empty service entry: the
    router still points at ``bai_service_{id}`` but it has no
    ``loadBalancer.servers``, so Traefik returns 503 for every request
    to this circuit until a later update succeeds.

    Same structural vulnerability as the incident's ``unload_traefik_circuit``
    partial-write: sequential RPCs that aren't atomic as a pair. The end
    symptom differs (503 downtime rather than cross-model routing)
    because the surviving piece after delete-first is the router, not a
    stale service. But the fix direction is the same — bundle the two
    operations into a single etcd transaction.
    """

    async def test_update_failure_does_not_leave_empty_service(
        self,
        circuit_manager: CircuitManager,
        fake_etcd: _FakeTraefikEtcd,
    ) -> None:
        """
        Seed the circuit, then drive an ``update_circuit_routes`` call
        whose atomic ``replace_prefix`` fails. The ConnectionError
        propagates up (update_circuit_routes has no retry), but because
        the replace is all-or-nothing, etcd retains the original
        service body — never an empty intermediate state.
        """
        circuit = _make_circuit(kernel_host="10.0.0.1", kernel_port=30000)
        await circuit_manager.initialize_traefik_circuits([circuit])
        service_prefix = f"worker_{WORKER_AUTHORITY}/http/services/bai_service_{circuit.id}"
        before = await fake_etcd.get_prefix(service_prefix)
        assert before, "precondition: the seed publish must place the service keys in etcd"

        fake_etcd.fail_on_replace_nth = 1

        with pytest.raises(ConnectionError):
            await circuit_manager.update_circuit_routes(circuit, [])

        after = await fake_etcd.get_prefix(service_prefix)
        assert after == before, (
            "atomic replace_prefix must leave the service subtree "
            "unchanged on failure; "
            f"got {len(after)} keys (before: {len(before)}). An "
            "intermediate empty service would cause Traefik to return "
            "503 for every request on this slot."
        )
