"""
Reproduction tests for the coordinator's Traefik-mode slot-level race.

Root cause: ``CircuitManager._circuit_locks`` is keyed by ``circuit_id``,
so two circuits that occupy the same Traefik slot (port or subdomain) get
independent locks. Worse, ``initialize_traefik_circuits`` acquires no lock
at all. Consequently ``initialize_traefik_circuits([circuit_B])`` and
``unload_circuits([circuit_A])`` on the same port X can interleave their
etcd writes freely. During the overlap Traefik's etcd holds two routers
(``bai_router_{A}`` and ``bai_router_{B}``) with the same ``rule``/
``entrypoints`` but pointing to different ``bai_service_{…}`` backends — so
the picking of which upstream handles an incoming request on port X becomes
nondeterministic until the ``delete_prefix`` for circuit_A is flushed.

These tests pin that down with ``asyncio.Event`` gates on the etcd mock so
the interleaving is deterministic rather than timing-dependent.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.appproxy.common.types import ProxyProtocol
from ai.backend.appproxy.coordinator.models import Circuit
from ai.backend.appproxy.coordinator.types import CircuitManager


@dataclass
class _FakeCircuit:
    """Minimal stand-in that satisfies the attribute surface used by
    ``initialize_traefik_circuits`` and ``unload_traefik_circuit``."""

    id: UUID
    worker_authority: str
    port: int | None = 8080
    subdomain: str | None = None
    protocol: ProxyProtocol = ProxyProtocol.HTTP

    @property
    def worker_row(self) -> SimpleNamespace:
        return SimpleNamespace(authority=self.worker_authority)

    @property
    def traefik_routers(self) -> dict[str, Any]:
        return {
            f"bai_router_{self.id}": {
                "rule": "Host(`proxy.example.com`)",
                "service": f"bai_service_{self.id}",
                "entrypoints": ["portproxy_8080"],
            }
        }

    @property
    def traefik_services(self) -> dict[str, Any]:
        return {
            f"bai_service_{self.id}": {
                "loadBalancer": {"servers": [{"url": "http://10.0.0.1:8000/"}]}
            }
        }

    def get_traefik_middlewares(self, _local_config: object) -> dict[str, Any]:
        return {}


def _make_circuit(worker: str = "worker-1") -> Circuit:
    return cast(Circuit, _FakeCircuit(id=uuid4(), worker_authority=worker))


@dataclass
class _EtcdCallRecorder:
    """Records put/delete_prefix calls in order and supports gating puts."""

    calls: list[tuple[str, str]] = field(default_factory=list)
    put_started: asyncio.Event = field(default_factory=asyncio.Event)
    release_put: asyncio.Event = field(default_factory=asyncio.Event)

    async def put_prefix(self, prefix: str, _data: Any) -> None:
        self.calls.append(("put_start", prefix))
        self.put_started.set()
        await self.release_put.wait()
        self.calls.append(("put_end", prefix))

    async def delete_prefix(self, prefix: str) -> None:
        self.calls.append(("delete", prefix))

    async def delete_prefixes(self, prefixes: list[str]) -> None:
        for prefix in prefixes:
            self.calls.append(("delete", prefix))

    async def get_prefix(self, _prefix: str) -> dict[str, Any]:
        return {}


class TestSlotMutexSerializesSameSlotCircuits:
    """
    Expected-after-fix behaviour: two circuits that share a slot must be
    mutually exclusive. Currently ``_circuit_locks`` is keyed by
    ``circuit_id`` rather than slot, so this test fails on HEAD; it will
    pass once a slot-scoped mutex is introduced.
    """

    @pytest.fixture
    def circuit_manager(self) -> CircuitManager:
        return CircuitManager(
            event_dispatcher=cast(Any, MagicMock()),
            event_producer=cast(Any, MagicMock()),
            traefik_etcd=cast(Any, AsyncMock()),
            local_config=cast(
                Any,
                SimpleNamespace(
                    proxy_coordinator=SimpleNamespace(enable_traefik=True),
                ),
            ),
        )

    async def test_second_same_slot_circuit_waits_until_first_releases(
        self, circuit_manager: CircuitManager
    ) -> None:
        """
        While the lock for circuit A (on slot X) is held, acquiring the
        lock for circuit B (also on slot X) must block.
        """
        circuit_a = _make_circuit()
        circuit_b = _make_circuit()  # same worker + same port as A ⇒ same slot

        b_acquired = asyncio.Event()

        async def acquire_b() -> None:
            async with circuit_manager.circuit_lock(circuit_b):
                b_acquired.set()

        async with circuit_manager.circuit_lock(circuit_a):
            task = asyncio.create_task(acquire_b())
            for _ in range(10):
                await asyncio.sleep(0)
            b_acquired_while_a_held = b_acquired.is_set()

        # Outside A's lock: B should now be able to acquire.
        try:
            await asyncio.wait_for(b_acquired.wait(), timeout=1.0)
        finally:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        assert not b_acquired_while_a_held, (
            "bug: circuit B acquired its lock while A's lock (same slot) "
            "was still held — slot-level mutual exclusion is missing, so "
            "create/unload for the same port/subdomain can interleave their "
            "etcd writes"
        )


class TestTraefikCreateAndUnloadDoNotSerialize:
    """
    Interleaving test: ``initialize_traefik_circuits`` takes no lock and
    ``unload_circuits`` takes a per-circuit (not per-slot) lock, so a
    create for circuit_B and an unload for circuit_A on the same port X
    overlap their etcd writes. Currently this manifests as a call log
    where ``delete_prefix`` for circuit_A is issued inside the
    ``put_prefix`` window of circuit_B's router — exactly the state that
    could leave two matching Traefik routers visible simultaneously.
    """

    WORKER_AUTHORITY = "worker-1"

    @pytest.fixture
    def recorder(self) -> _EtcdCallRecorder:
        return _EtcdCallRecorder()

    @pytest.fixture
    def circuit_manager(self, recorder: _EtcdCallRecorder) -> CircuitManager:
        etcd = MagicMock()
        etcd.put_prefix = AsyncMock(side_effect=recorder.put_prefix)
        etcd.delete_prefix = AsyncMock(side_effect=recorder.delete_prefix)
        etcd.delete_prefixes = AsyncMock(side_effect=recorder.delete_prefixes)
        etcd.get_prefix = AsyncMock(side_effect=recorder.get_prefix)
        return CircuitManager(
            event_dispatcher=cast(Any, MagicMock()),
            event_producer=cast(Any, MagicMock()),
            traefik_etcd=cast(Any, etcd),
            local_config=cast(
                Any,
                SimpleNamespace(
                    proxy_coordinator=SimpleNamespace(enable_traefik=True),
                ),
            ),
        )

    @pytest.fixture
    def circuit_a(self) -> Circuit:
        return _make_circuit(worker=self.WORKER_AUTHORITY)

    @pytest.fixture
    def circuit_b(self) -> Circuit:
        return _make_circuit(worker=self.WORKER_AUTHORITY)

    async def test_no_delete_interleaves_with_put_on_same_slot(
        self,
        circuit_manager: CircuitManager,
        circuit_a: Circuit,
        circuit_b: Circuit,
        recorder: _EtcdCallRecorder,
    ) -> None:
        """
        Expected-after-fix: when a create for circuit_B and an unload for
        circuit_A target the same slot, their etcd writes must not
        interleave. Concretely, no ``delete_prefix`` for circuit_A should
        appear inside circuit_B's ``put_prefix`` window (or vice versa) —
        otherwise there is a moment where Traefik's etcd view contains two
        routers matching the same traffic.

        On HEAD this assertion fails: ``initialize_traefik_circuits`` holds
        no lock and ``unload_circuits`` takes a per-circuit lock, so the
        deletes for A are issued while ``put_prefix`` for B is still in
        flight.
        """
        create_task = asyncio.create_task(circuit_manager.initialize_traefik_circuits([circuit_b]))
        # Park put_prefix(B) inside the gate so we can observe whether a
        # concurrent unload on the same slot is serialized behind it.
        await recorder.put_started.wait()

        unload_task = asyncio.create_task(circuit_manager.unload_circuits([circuit_a]))

        for _ in range(10):
            await asyncio.sleep(0)

        recorder.release_put.set()
        await asyncio.gather(create_task, unload_task)

        put_start_idx = next(i for i, (op, _) in enumerate(recorder.calls) if op == "put_start")
        put_end_idx = next(i for i, (op, _) in enumerate(recorder.calls) if op == "put_end")
        interleaved_deletes = [
            (i, prefix)
            for i, (op, prefix) in enumerate(recorder.calls)
            if op == "delete" and put_start_idx < i < put_end_idx
        ]
        assert not interleaved_deletes, (
            "bug: delete_prefix calls were issued while put_prefix for the "
            "same slot was still in flight — during this window Traefik's "
            "etcd view would hold two routers pointing at different "
            f"services. Interleaved deletes: {interleaved_deletes}. "
            f"Full call log: {recorder.calls}"
        )
