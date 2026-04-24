"""
Reproduction tests for the app-proxy worker slot-level race condition.

The race: ``BaseFrontend.register_circuit`` has an ``await`` point between
assigning ``self.circuits[key] = circuit`` (synchronous) and
``self.backends[key] = await self.initialize_backend(...)``. While the second
await is suspended, the port/subdomain slot is in an inconsistent state:

    circuits[key] = <new circuit B>
    backends[key] = <old backend A>     # not yet replaced

A concurrent request passing through ``ensure_slot_middleware`` at that moment
reads both dicts non-atomically and ends up with
``request["circuit"] == circuit_B`` paired with ``request["backend"]`` whose
``.circuit`` is still ``circuit_A`` — i.e. a request intended for one model
is about to be forwarded to a backend that belongs to a different circuit.

These tests pin that window down deterministically with an ``asyncio.Event``
so the reproduction is not timing-dependent.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
import pytest_mock
from aiohttp import web

from ai.backend.appproxy.common.types import (
    AppMode,
    FrontendMode,
    ProxyProtocol,
    RouteInfo,
)
from ai.backend.appproxy.worker.proxy.backend.http import HTTPBackend
from ai.backend.appproxy.worker.proxy.frontend.http.port import PortFrontend
from ai.backend.appproxy.worker.types import (
    Circuit,
    InferenceAppInfo,
    PortFrontendInfo,
)
from ai.backend.common.types import RuntimeVariant


def _make_route(kernel_host: str, kernel_port: int) -> RouteInfo:
    return RouteInfo(
        route_id=uuid4(),
        session_id=uuid4(),
        session_name=None,
        kernel_host=kernel_host,
        kernel_port=kernel_port,
        protocol=ProxyProtocol.HTTP,
        traffic_ratio=1.0,
    )


def _make_circuit(port: int, app_name: str) -> Circuit:
    """Circuit with ``open_to_public=True`` so ensure_credential is a no-op."""
    route = _make_route(kernel_host="10.0.0.1", kernel_port=8080)
    return Circuit(
        id=uuid4(),
        app=app_name,
        protocol=ProxyProtocol.HTTP,
        worker=UUID("00000000-0000-0000-0000-000000000000"),
        app_mode=AppMode.INFERENCE,
        frontend_mode=FrontendMode.PORT,
        frontend=PortFrontendInfo(port),
        port=port,
        app_info=InferenceAppInfo(
            endpoint_id=uuid4(),
            runtime_variant=RuntimeVariant("vllm"),
        ),
        subdomain=None,
        runtime_variant=RuntimeVariant("vllm"),
        envs={},
        arguments=None,
        open_to_public=True,
        allowed_client_ips=None,
        user_id=uuid4(),
        access_key="TESTKEY",
        endpoint_id=None,
        route_info=[route],
        session_ids=[route.session_id],
        created_at=datetime(2024, 7, 16, 5, 45, 45, tzinfo=UTC),
        updated_at=datetime(2024, 7, 16, 5, 45, 45, tzinfo=UTC),
    )


class _FakeRequest(dict[str, Any]):
    """Minimal stand-in for ``aiohttp.web.Request`` used by ensure_slot_middleware.

    The middleware only needs:
      * ``request.app["port"]`` to look up the slot
      * mutable mapping semantics for ``request["circuit"] = ...``
    """

    def __init__(self, app: dict[str, Any]) -> None:
        super().__init__()
        self.app = app


class TestRegisterCircuitSlotRace:
    """Race window exposed during ``register_circuit``'s second await."""

    FRONTEND_PORT = 10200

    @pytest.fixture
    def port_frontend(self, mocker: pytest_mock.MockerFixture) -> PortFrontend:
        frontend = PortFrontend(root_context=mocker.MagicMock())
        frontend.circuits = {}
        frontend.backends = {}
        return frontend

    @pytest.fixture
    def circuit_a(self) -> Circuit:
        return _make_circuit(port=self.FRONTEND_PORT, app_name="model-a")

    @pytest.fixture
    def circuit_b(self) -> Circuit:
        return _make_circuit(port=self.FRONTEND_PORT, app_name="model-b")

    @pytest.fixture
    def backend_a(self, circuit_a: Circuit) -> MagicMock:
        backend = MagicMock(spec=HTTPBackend)
        backend.circuit = circuit_a
        return backend

    @pytest.fixture
    def backend_b(self, circuit_b: Circuit) -> MagicMock:
        backend = MagicMock(spec=HTTPBackend)
        backend.circuit = circuit_b
        return backend

    @pytest.fixture
    def frontend_with_circuit_a(
        self,
        port_frontend: PortFrontend,
        circuit_a: Circuit,
        backend_a: MagicMock,
    ) -> PortFrontend:
        """Pre-registered slot state: circuits[port]=A, backends[port]=backend_A."""
        port_frontend.circuits[self.FRONTEND_PORT] = circuit_a
        port_frontend.backends[self.FRONTEND_PORT] = backend_a
        return port_frontend

    async def test_circuit_and_backend_mismatch_during_register(
        self,
        frontend_with_circuit_a: PortFrontend,
        circuit_a: Circuit,
        circuit_b: Circuit,
        backend_a: MagicMock,
        backend_b: MagicMock,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        """
        While ``register_circuit(circuit_B)`` is mid-flight (parked inside
        ``initialize_backend``), a concurrent request going through
        ``ensure_slot_middleware`` must never observe a circuit paired with
        a backend that belongs to a different circuit.

        Before the fix, ``register_circuit`` assigned
        ``self.circuits[key] = circuit`` (sync) before awaiting
        ``initialize_backend``, leaving a window where ``circuits[port]``
        was circuit_B but ``backends[port]`` was still backend_A.
        """
        frontend = frontend_with_circuit_a
        port = self.FRONTEND_PORT

        release_initialize = asyncio.Event()
        initialize_entered = asyncio.Event()

        async def gated_initialize_backend(circuit: Circuit, routes: list[RouteInfo]) -> MagicMock:
            initialize_entered.set()
            await release_initialize.wait()
            return backend_b

        async def noop_terminate_backend(_backend: object) -> None:
            return None

        mocker.patch.object(frontend, "initialize_backend", side_effect=gated_initialize_backend)
        mocker.patch.object(frontend, "terminate_backend", side_effect=noop_terminate_backend)

        # Kick off the new-circuit registration; it will park inside initialize_backend.
        register_task = asyncio.create_task(frontend.register_circuit(circuit_b, []))
        await initialize_entered.wait()

        # A concurrent request passes through the middleware while register_circuit
        # is still in progress. Whatever pair it observes must be self-consistent.
        request = _FakeRequest(app={"port": port})
        handler = AsyncMock(return_value=MagicMock(spec=web.StreamResponse))

        await frontend.ensure_slot_middleware(cast(web.Request, request), handler)

        observed_circuit: Circuit = request["circuit"]
        observed_backend: HTTPBackend = request["backend"]
        assert observed_circuit.id == observed_backend.circuit.id, (
            "slot race: request[circuit].id="
            f"{observed_circuit.id} (app={observed_circuit.app}) "
            "but request[backend].circuit.id="
            f"{observed_backend.circuit.id} (app={observed_backend.circuit.app}) — "
            "request would be proxied to a backend that belongs to a different circuit"
        )

        # Cleanup: let register_circuit finish.
        release_initialize.set()
        await register_task

    async def test_middleware_sees_consistent_pair_outside_race_window(
        self,
        frontend_with_circuit_a: PortFrontend,
        circuit_a: Circuit,
        backend_a: MagicMock,
    ) -> None:
        """Sanity: without an ongoing register_circuit, the pair is consistent.

        This pins down that the mismatch in the sister test is caused by the
        race window, not by fixture plumbing.
        """
        frontend = frontend_with_circuit_a

        async def handler(_request: web.Request) -> web.StreamResponse:
            return MagicMock(spec=web.StreamResponse)

        request = _FakeRequest(app={"port": self.FRONTEND_PORT})
        await frontend.ensure_slot_middleware(cast(web.Request, request), handler)

        assert request["circuit"].id == circuit_a.id
        assert request["backend"] is backend_a
        assert request["circuit"].id == request["backend"].circuit.id


class TestBreakRegisterSlotRace:
    """
    ``break_circuit`` and ``register_circuit`` currently have no mutual
    exclusion at the worker level. When they target the same slot
    concurrently, the worker's in-memory state can be corrupted:

      * ``break(A)`` parked at its ``await terminate_backend(...)`` keeps a
        local reference to ``backend_A``, and its ``finally`` clause will
        unconditionally run ``del self.backends[key]`` / ``del
        self.circuits[key]`` after the await returns — wiping whatever a
        concurrent ``register(B)`` swapped in for the same key.
      * Two concurrent ``break(A)`` calls both pass the stale-check before
        either reaches the finally; the second one's ``del`` then hits a
        ``KeyError`` because the first already removed the key.

    These tests pin those windows down deterministically. The fix is a
    slot-level ``asyncio.Lock`` around ``register_circuit`` /
    ``break_circuit`` / ``update_circuit_route_info``.
    """

    FRONTEND_PORT = 10300

    @pytest.fixture
    def port_frontend(self, mocker: pytest_mock.MockerFixture) -> PortFrontend:
        frontend = PortFrontend(root_context=mocker.MagicMock())
        frontend.circuits = {}
        frontend.backends = {}
        return frontend

    @pytest.fixture
    def circuit_a(self) -> Circuit:
        return _make_circuit(port=self.FRONTEND_PORT, app_name="model-a")

    @pytest.fixture
    def circuit_b(self) -> Circuit:
        return _make_circuit(port=self.FRONTEND_PORT, app_name="model-b")

    @pytest.fixture
    def backend_a(self, circuit_a: Circuit) -> MagicMock:
        backend = MagicMock(spec=HTTPBackend)
        backend.circuit = circuit_a
        return backend

    @pytest.fixture
    def backend_b(self, circuit_b: Circuit) -> MagicMock:
        backend = MagicMock(spec=HTTPBackend)
        backend.circuit = circuit_b
        return backend

    @pytest.fixture
    def frontend_with_circuit_a(
        self,
        port_frontend: PortFrontend,
        circuit_a: Circuit,
        backend_a: MagicMock,
    ) -> PortFrontend:
        port_frontend.circuits[self.FRONTEND_PORT] = circuit_a
        port_frontend.backends[self.FRONTEND_PORT] = backend_a
        return port_frontend

    async def test_break_finally_must_not_wipe_a_concurrent_register(
        self,
        frontend_with_circuit_a: PortFrontend,
        circuit_a: Circuit,
        circuit_b: Circuit,
        backend_a: MagicMock,
        backend_b: MagicMock,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        """
        break(A) is parked at its ``await terminate_backend(backend_A)``
        call. While parked, register(B) completes its atomic swap, so the
        slot now holds (circuit_B, backend_B). When we then release the
        terminate gate, break(A)'s ``finally`` clause runs and —
        unconditionally — ``del``\\ s circuits[key] and backends[key],
        wiping circuit_B's state.

        After a slot-level mutex is introduced, break and register on the
        same slot serialize, so break completes before register begins and
        the final state correctly reflects register's output.
        """
        frontend = frontend_with_circuit_a
        port = self.FRONTEND_PORT

        release_terminate = asyncio.Event()
        terminate_calls: list[object] = []

        async def gated_terminate_backend(backend: object) -> None:
            terminate_calls.append(backend)
            await release_terminate.wait()

        async def instant_initialize_backend(
            _circuit: Circuit, _routes: list[RouteInfo]
        ) -> MagicMock:
            return backend_b

        mocker.patch.object(frontend, "terminate_backend", side_effect=gated_terminate_backend)
        mocker.patch.object(frontend, "initialize_backend", side_effect=instant_initialize_backend)

        # break(A) runs first and parks at terminate(backend_A).
        break_task = asyncio.create_task(frontend.break_circuit(circuit_a))
        for _ in range(5):
            await asyncio.sleep(0)
        assert backend_a in terminate_calls, (
            "precondition: break should have reached terminate_backend"
        )

        # While break is parked, register(B) runs to completion of its
        # atomic swap (and itself parks at terminate(old=backend_A)).
        register_task = asyncio.create_task(frontend.register_circuit(circuit_b, []))
        for _ in range(5):
            await asyncio.sleep(0)

        # Release the gate — break's finally now runs and deletes the slot
        # state that register just populated.
        release_terminate.set()
        await asyncio.gather(break_task, register_task)

        assert port in frontend.circuits, (
            "slot race: break(A)'s finally wiped the slot after register(B) "
            "had already swapped in its state. Subsequent requests to this "
            "port would fail with 'Unregistered slot' even though "
            "register_circuit(B) completed successfully."
        )
        assert frontend.circuits[port].id == circuit_b.id
        assert frontend.backends[port] is backend_b

    async def test_concurrent_double_break_must_not_raise(
        self,
        frontend_with_circuit_a: PortFrontend,
        circuit_a: Circuit,
        backend_a: MagicMock,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        """
        Two concurrent break(A) calls both pass the stale check before
        either reaches its ``finally``. The second one's ``del
        backends[key]`` then raises ``KeyError`` because the first already
        removed the key. With a slot mutex, the second break sees the
        slot gone at the top of the function and returns cleanly.
        """
        frontend = frontend_with_circuit_a

        release_terminate = asyncio.Event()

        async def gated_terminate_backend(_backend: object) -> None:
            await release_terminate.wait()

        mocker.patch.object(frontend, "terminate_backend", side_effect=gated_terminate_backend)

        break_task_1 = asyncio.create_task(frontend.break_circuit(circuit_a))
        break_task_2 = asyncio.create_task(frontend.break_circuit(circuit_a))
        for _ in range(5):
            await asyncio.sleep(0)

        release_terminate.set()
        results = await asyncio.gather(break_task_1, break_task_2, return_exceptions=True)

        for idx, result in enumerate(results):
            assert not isinstance(result, BaseException), (
                f"break task #{idx} raised {type(result).__name__}: {result!r} — "
                "concurrent break(A) calls are not serialized, so the "
                "loser's ``del`` trips over an already-removed key"
            )
