"""Tests for on_reconcile_traefik_routes event handler."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.appproxy.common.events import DoReconcileTraefikRoutesEvent
from ai.backend.appproxy.common.types import AppMode, ProxyProtocol
from ai.backend.appproxy.coordinator.models import Circuit, Worker
from ai.backend.appproxy.coordinator.server import on_reconcile_traefik_routes
from ai.backend.appproxy.coordinator.types import CircuitManager
from ai.backend.common.types import AgentId


class _ReadonlySession:
    async def __aenter__(self) -> object:
        return object()

    async def __aexit__(self, *_exc: object) -> None:
        return None


class _FakeDB:
    def begin_readonly_session(self) -> _ReadonlySession:
        return _ReadonlySession()


def _make_context(
    enable_traefik: bool,
    circuit_manager: Any,
) -> Any:
    """Build a minimal RootContext-shaped object sufficient for the handler."""
    return SimpleNamespace(
        local_config=SimpleNamespace(
            proxy_coordinator=SimpleNamespace(enable_traefik=enable_traefik),
        ),
        db=_FakeDB(),
        circuit_manager=circuit_manager,
    )


@asynccontextmanager
async def _noop_lock(_circuit_id: object) -> AsyncIterator[None]:
    yield


def _make_circuit(app_mode: AppMode, worker_authority: str = "worker-1") -> Circuit:
    circuit: Any = MagicMock(spec=Circuit)
    circuit.id = uuid4()
    circuit.app_mode = app_mode
    circuit.route_info = []
    circuit.protocol = ProxyProtocol.HTTP
    circuit.worker_row = SimpleNamespace(authority=worker_authority)
    return cast(Circuit, circuit)


def _make_worker(authority: str = "worker-1") -> Worker:
    worker: Any = MagicMock(spec=Worker)
    worker.authority = authority
    return cast(Worker, worker)


class TestOnReconcileTraefikRoutes:
    @pytest.fixture
    def circuit_manager(self) -> Any:
        manager = MagicMock()
        manager.update_circuit_routes = AsyncMock()
        manager.reconcile_traefik_etcd_state = AsyncMock()
        manager.circuit_lock = _noop_lock
        return manager

    async def test_noop_when_traefik_disabled(
        self,
        circuit_manager: Any,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        circuits = [_make_circuit(AppMode.INFERENCE)]
        workers = [_make_worker()]
        context = _make_context(enable_traefik=False, circuit_manager=circuit_manager)

        list_circuits_mock = AsyncMock(return_value=circuits)
        list_workers_mock = AsyncMock(return_value=workers)
        monkeypatch.setattr(Circuit, "list_circuits", list_circuits_mock)
        monkeypatch.setattr(Worker, "list_workers", list_workers_mock)

        await on_reconcile_traefik_routes(context, AgentId("test"), DoReconcileTraefikRoutesEvent())

        assert circuit_manager.update_circuit_routes.await_count == 0
        assert circuit_manager.reconcile_traefik_etcd_state.await_count == 0
        assert list_circuits_mock.await_count == 0
        assert list_workers_mock.await_count == 0

    async def test_reconciles_both_inference_and_interactive_circuits(
        self,
        circuit_manager: Any,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Regression: previous version skipped interactive circuits with
        # `if circuit.app_mode != AppMode.INFERENCE: continue`. The new handler
        # must include both so neither lifecycle goes un-reconciled.
        inference = _make_circuit(AppMode.INFERENCE)
        interactive = _make_circuit(AppMode.INTERACTIVE)
        circuits = [inference, interactive]
        workers = [_make_worker()]
        context = _make_context(enable_traefik=True, circuit_manager=circuit_manager)

        monkeypatch.setattr(Circuit, "list_circuits", AsyncMock(return_value=circuits))
        monkeypatch.setattr(Worker, "list_workers", AsyncMock(return_value=workers))

        await on_reconcile_traefik_routes(context, AgentId("test"), DoReconcileTraefikRoutesEvent())

        assert circuit_manager.update_circuit_routes.await_count == 2
        called_circuits = {
            call.args[0] for call in circuit_manager.update_circuit_routes.await_args_list
        }
        assert called_circuits == {inference, interactive}

    async def test_calls_stale_cleanup_after_put_reconcile(
        self,
        circuit_manager: Any,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        circuits = [_make_circuit(AppMode.INFERENCE)]
        workers = [_make_worker("worker-1"), _make_worker("worker-2")]
        context = _make_context(enable_traefik=True, circuit_manager=circuit_manager)

        monkeypatch.setattr(Circuit, "list_circuits", AsyncMock(return_value=circuits))
        monkeypatch.setattr(Worker, "list_workers", AsyncMock(return_value=workers))

        await on_reconcile_traefik_routes(context, AgentId("test"), DoReconcileTraefikRoutesEvent())

        # Stale cleanup was invoked with both circuit list and worker list.
        assert circuit_manager.reconcile_traefik_etcd_state.await_count == 1
        call = circuit_manager.reconcile_traefik_etcd_state.await_args
        assert list(call.args[0]) == circuits
        assert list(call.args[1]) == workers

    async def test_stale_cleanup_errors_do_not_break_cycle(
        self,
        circuit_manager: Any,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        circuits = [_make_circuit(AppMode.INFERENCE)]
        workers = [_make_worker()]
        context = _make_context(enable_traefik=True, circuit_manager=circuit_manager)

        monkeypatch.setattr(Circuit, "list_circuits", AsyncMock(return_value=circuits))
        monkeypatch.setattr(Worker, "list_workers", AsyncMock(return_value=workers))
        circuit_manager.reconcile_traefik_etcd_state = AsyncMock(
            side_effect=RuntimeError("etcd down")
        )

        # Must not raise — per-phase errors are swallowed.
        await on_reconcile_traefik_routes(context, AgentId("test"), DoReconcileTraefikRoutesEvent())

        assert circuit_manager.update_circuit_routes.await_count == 1

    async def test_handler_continues_after_per_circuit_failure(
        self,
        circuit_manager: Any,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        first = _make_circuit(AppMode.INFERENCE)
        second = _make_circuit(AppMode.INFERENCE)
        circuits = [first, second]
        workers = [_make_worker()]
        context = _make_context(enable_traefik=True, circuit_manager=circuit_manager)

        monkeypatch.setattr(Circuit, "list_circuits", AsyncMock(return_value=circuits))
        monkeypatch.setattr(Worker, "list_workers", AsyncMock(return_value=workers))

        circuit_manager.update_circuit_routes = AsyncMock(
            side_effect=[RuntimeError("etcd down"), None]
        )

        await on_reconcile_traefik_routes(context, AgentId("test"), DoReconcileTraefikRoutesEvent())

        assert circuit_manager.update_circuit_routes.await_count == 2
        # Stale cleanup still runs after a per-circuit failure.
        assert circuit_manager.reconcile_traefik_etcd_state.await_count == 1


class TestReconcileTraefikEtcdState:
    """Unit tests for CircuitManager.reconcile_traefik_etcd_state stale detection."""

    def _make_manager(self, traefik_etcd: Any) -> Any:
        return CircuitManager(
            event_dispatcher=cast(Any, MagicMock()),
            event_producer=cast(Any, MagicMock()),
            traefik_etcd=traefik_etcd,
            local_config=cast(
                Any,
                SimpleNamespace(proxy_coordinator=SimpleNamespace(enable_traefik=True)),
            ),
        )

    async def test_drops_stale_circuit_missing_from_db(self) -> None:
        live_id = uuid4()
        stale_id = uuid4()

        # etcd currently has both under http; DB only knows about live_id.
        # Return the circuits only for http and empty for tcp so the tcp-scope
        # pass does not mis-classify live_id as stale.
        async def get_prefix_side_effect(prefix: str) -> dict[str, Any]:
            if prefix == "worker_worker-1/http/services":
                return {
                    f"bai_service_{live_id}": {"loadBalancer": {"servers": {}}},
                    f"bai_service_{stale_id}": {"loadBalancer": {"servers": {}}},
                }
            return {}

        get_prefix_mock = AsyncMock(side_effect=get_prefix_side_effect)
        delete_prefix_mock = AsyncMock()

        traefik_etcd = MagicMock()
        traefik_etcd.get_prefix = get_prefix_mock
        traefik_etcd.delete_prefix = delete_prefix_mock

        manager = self._make_manager(traefik_etcd)

        live_circuit: Any = MagicMock(spec=Circuit)
        live_circuit.id = live_id
        live_circuit.protocol = ProxyProtocol.HTTP
        live_circuit.worker_row = SimpleNamespace(authority="worker-1")

        worker = _make_worker("worker-1")

        await manager.reconcile_traefik_etcd_state([live_circuit], [worker])

        # We must have deleted exactly the stale circuit's router / service /
        # middleware prefixes — and *not* the live circuit's.
        deleted_prefixes = {call.args[0] for call in delete_prefix_mock.await_args_list}
        expected_stale = {
            f"worker_worker-1/http/routers/bai_router_{stale_id}",
            f"worker_worker-1/http/services/bai_service_{stale_id}",
            f"worker_worker-1/http/middlewares/bai_appproxy_plugin_{stale_id}",
            f"worker_worker-1/http/middlewares/appproxy/plugin/bai_appproxy_plugin_{stale_id}",
        }
        assert expected_stale.issubset(deleted_prefixes)
        for prefix in deleted_prefixes:
            # None of the deleted prefixes should reference the live circuit.
            assert str(live_id) not in prefix

    async def test_noop_when_etcd_empty(self) -> None:
        get_prefix_mock = AsyncMock(return_value={})
        delete_prefix_mock = AsyncMock()
        traefik_etcd = MagicMock()
        traefik_etcd.get_prefix = get_prefix_mock
        traefik_etcd.delete_prefix = delete_prefix_mock

        manager = self._make_manager(traefik_etcd)

        live_circuit: Any = MagicMock(spec=Circuit)
        live_circuit.id = uuid4()
        live_circuit.protocol = ProxyProtocol.HTTP
        live_circuit.worker_row = SimpleNamespace(authority="worker-1")

        await manager.reconcile_traefik_etcd_state([live_circuit], [_make_worker("worker-1")])

        assert delete_prefix_mock.await_count == 0

    async def test_noop_when_etcd_only_has_live_circuits(self) -> None:
        live_id = uuid4()

        async def get_prefix_side_effect(prefix: str) -> dict[str, Any]:
            if prefix == "worker_worker-1/http/services":
                return {f"bai_service_{live_id}": {"loadBalancer": {"servers": {}}}}
            return {}

        get_prefix_mock = AsyncMock(side_effect=get_prefix_side_effect)
        delete_prefix_mock = AsyncMock()
        traefik_etcd = MagicMock()
        traefik_etcd.get_prefix = get_prefix_mock
        traefik_etcd.delete_prefix = delete_prefix_mock

        manager = self._make_manager(traefik_etcd)

        live_circuit: Any = MagicMock(spec=Circuit)
        live_circuit.id = live_id
        live_circuit.protocol = ProxyProtocol.HTTP
        live_circuit.worker_row = SimpleNamespace(authority="worker-1")

        await manager.reconcile_traefik_etcd_state([live_circuit], [_make_worker("worker-1")])

        assert delete_prefix_mock.await_count == 0

    async def test_ignores_non_bai_service_keys(self) -> None:
        # Keys that do not match bai_service_{uuid} pattern must be ignored
        # so unrelated third-party keys under the same prefix are never
        # considered stale.
        get_prefix_mock = AsyncMock(
            return_value={
                "bai_service_not-a-uuid": {"loadBalancer": {}},
                "some_other_key": {"x": "y"},
                "": "",
            }
        )
        delete_prefix_mock = AsyncMock()
        traefik_etcd = MagicMock()
        traefik_etcd.get_prefix = get_prefix_mock
        traefik_etcd.delete_prefix = delete_prefix_mock

        manager = self._make_manager(traefik_etcd)

        await manager.reconcile_traefik_etcd_state([], [_make_worker("worker-1")])

        assert delete_prefix_mock.await_count == 0

    async def test_skips_tcp_middlewares_when_dropping_stale(self) -> None:
        stale_id = uuid4()
        # get_prefix is called twice per worker (http and tcp). Return the
        # stale circuit only under the tcp scope to verify middleware cleanup
        # is skipped for non-HTTP protocols.
        call_responses: dict[str, dict[str, Any]] = {
            "worker_worker-1/http/services": {},
            "worker_worker-1/tcp/services": {
                f"bai_service_{stale_id}": {"loadBalancer": {"servers": {}}}
            },
        }

        async def get_prefix_side_effect(prefix: str) -> dict[str, Any]:
            return call_responses.get(prefix, {})

        get_prefix_mock = AsyncMock(side_effect=get_prefix_side_effect)
        delete_prefix_mock = AsyncMock()
        traefik_etcd = MagicMock()
        traefik_etcd.get_prefix = get_prefix_mock
        traefik_etcd.delete_prefix = delete_prefix_mock

        manager = self._make_manager(traefik_etcd)

        await manager.reconcile_traefik_etcd_state([], [_make_worker("worker-1")])

        deleted_prefixes = {call.args[0] for call in delete_prefix_mock.await_args_list}
        # TCP must delete router + service only, no middlewares.
        assert f"worker_worker-1/tcp/routers/bai_router_{stale_id}" in deleted_prefixes
        assert f"worker_worker-1/tcp/services/bai_service_{stale_id}" in deleted_prefixes
        for prefix in deleted_prefixes:
            assert "middlewares" not in prefix


def _unused_uuid() -> UUID:
    # Keep UUID imported for type checkers even if unused elsewhere.
    return uuid4()
