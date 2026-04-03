from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.appproxy.common.errors import ObjectNotFound
from ai.backend.appproxy.coordinator.health_checker import HealthCheckEngine
from ai.backend.appproxy.coordinator.models import Circuit
from ai.backend.appproxy.coordinator.types import CircuitManager


class _ReadonlySessionContext:
    def __init__(self, order: list[str]) -> None:
        self._order = order

    async def __aenter__(self) -> object:
        self._order.append("db_enter")
        return object()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: Any,
    ) -> None:
        self._order.append("db_exit")


class _FakeDB:
    def __init__(self, order: list[str]) -> None:
        self._order = order

    def begin_readonly_session(self) -> _ReadonlySessionContext:
        return _ReadonlySessionContext(self._order)


class _FakeCircuitManager:
    def __init__(self, order: list[str]) -> None:
        self._order = order

    @asynccontextmanager
    async def circuit_lock(self, _circuit_id: UUID) -> AsyncIterator[None]:
        self._order.append("lock_enter")
        try:
            yield
        finally:
            self._order.append("lock_exit")

    def release_circuit_lock(self, _circuit_id: UUID) -> None:
        self._order.append("release_lock")

    async def _update_circuit_routes_unlocked(
        self,
        _circuit: object,
        _old_routes: list[object],
    ) -> None:
        self._order.append("update")


@dataclass
class UpdateControl:
    """Control handle for a two-invocation fake update side effect."""

    first_started: asyncio.Event = field(default_factory=asyncio.Event)
    release_first: asyncio.Event = field(default_factory=asyncio.Event)
    call_order: list[str] = field(default_factory=list)
    _invocation_count: int = field(default=0, init=False)

    async def side_effect(self, _circuit: object, _old_routes: list[object]) -> None:
        self._invocation_count += 1
        if self._invocation_count == 1:
            self.call_order.append("first_start")
            self.first_started.set()
            await self.release_first.wait()
            self.call_order.append("first_end")
            return
        self.call_order.append("second_start")
        self.call_order.append("second_end")


class TestCircuitManagerLocking:
    @pytest.fixture
    def circuit_manager(self) -> CircuitManager:
        return CircuitManager(
            event_dispatcher=cast(Any, MagicMock()),
            event_producer=cast(Any, MagicMock()),
            traefik_etcd=None,
            local_config=cast(
                Any,
                SimpleNamespace(
                    proxy_coordinator=SimpleNamespace(enable_traefik=True),
                ),
            ),
        )

    @pytest.fixture
    def circuit(self) -> Circuit:
        return cast(Circuit, SimpleNamespace(id=uuid4()))

    @pytest.fixture
    def update_control(self) -> UpdateControl:
        return UpdateControl()

    @pytest.fixture
    def patched_update(
        self,
        circuit_manager: CircuitManager,
        update_control: UpdateControl,
        monkeypatch: pytest.MonkeyPatch,
    ) -> UpdateControl:
        monkeypatch.setattr(
            circuit_manager,
            "update_traefik_circuit_routes",
            AsyncMock(side_effect=update_control.side_effect),
        )
        return update_control

    async def test_same_circuit_updates_are_serialized(
        self,
        circuit_manager: CircuitManager,
        circuit: Circuit,
        patched_update: UpdateControl,
    ) -> None:
        # Act
        first_task = asyncio.create_task(circuit_manager.update_circuit_routes(circuit, []))
        await patched_update.first_started.wait()

        second_task = asyncio.create_task(circuit_manager.update_circuit_routes(circuit, []))
        await asyncio.sleep(0)

        # Assert - second update must wait for first
        assert patched_update.call_order == ["first_start"]

        patched_update.release_first.set()
        await asyncio.gather(first_task, second_task)

        assert patched_update.call_order == [
            "first_start",
            "first_end",
            "second_start",
            "second_end",
        ]

    async def test_queued_updates_before_unload_are_serialized(
        self,
        circuit_manager: CircuitManager,
        circuit: Circuit,
        patched_update: UpdateControl,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(circuit_manager, "unload_traefik_circuit", AsyncMock(return_value=None))

        # Act - hold the lock externally, then queue update + unload behind it
        async with circuit_manager.circuit_lock(circuit.id):
            first_update_task = asyncio.create_task(
                circuit_manager.update_circuit_routes(circuit, [])
            )
            second_update_task = asyncio.create_task(
                circuit_manager.update_circuit_routes(circuit, [])
            )
            unload_task = asyncio.create_task(circuit_manager.unload_circuits([circuit]))
            await asyncio.sleep(0)

        # First update acquires the lock
        await patched_update.first_started.wait()
        assert patched_update.call_order == ["first_start"]

        # Release first update — second update and unload proceed in queue order
        patched_update.release_first.set()
        await asyncio.gather(first_update_task, second_update_task, unload_task)

        assert patched_update.call_order == [
            "first_start",
            "first_end",
            "second_start",
            "second_end",
        ]
        # Lock entry is cleaned up after unload
        assert circuit.id not in circuit_manager._circuit_locks

    @pytest.fixture
    def patch_unload(
        self,
        circuit_manager: CircuitManager,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(circuit_manager, "unload_traefik_circuit", AsyncMock(return_value=None))

    async def test_unload_removes_circuit_lock(
        self,
        circuit_manager: CircuitManager,
        circuit: Circuit,
        patch_unload: None,
    ) -> None:
        # Populate the lock entry
        async with circuit_manager.circuit_lock(circuit.id):
            pass
        assert circuit.id in circuit_manager._circuit_locks

        # Act
        await circuit_manager.unload_circuits([circuit])

        # Assert - lock entry should be cleaned up
        assert circuit.id not in circuit_manager._circuit_locks


class TestHealthCheckEnginePropagation:
    @pytest.fixture
    def operation_order(self) -> list[str]:
        return []

    @pytest.fixture
    def fake_circuit_manager(self, operation_order: list[str]) -> _FakeCircuitManager:
        return _FakeCircuitManager(operation_order)

    @pytest.fixture
    def health_check_engine(
        self,
        operation_order: list[str],
        fake_circuit_manager: _FakeCircuitManager,
    ) -> HealthCheckEngine:
        return HealthCheckEngine(
            db=cast(Any, _FakeDB(operation_order)),
            event_producer=cast(Any, MagicMock()),
            valkey_live=cast(Any, MagicMock()),
            circuit_manager=cast(Any, fake_circuit_manager),
            health_check_timer_interval=1.0,
            valkey_schedule=cast(Any, MagicMock()),
        )

    @pytest.fixture
    def _patch_circuit_get(
        self,
        operation_order: list[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        async def _fake_get(
            _session: object,
            requested_circuit_id: UUID,
            load_worker: bool = True,
            load_endpoint: bool = True,
        ) -> object:
            assert load_worker is True
            assert load_endpoint is True
            operation_order.append("circuit_get")
            return SimpleNamespace(
                id=requested_circuit_id,
                endpoint_id=None,
                endpoint_row=None,
                route_info=[],
                healthy_routes=[],
            )

        monkeypatch.setattr(Circuit, "get", _fake_get)

    async def test_fresh_read_happens_under_circuit_lock(
        self,
        health_check_engine: HealthCheckEngine,
        operation_order: list[str],
        _patch_circuit_get: None,
    ) -> None:
        circuit_id = uuid4()

        # Act
        await health_check_engine.propagate_route_updates_to_workers(
            cast(Any, SimpleNamespace(id=circuit_id)),
            [],
        )

        # Assert - DB read and route update must happen inside circuit lock
        assert operation_order == [
            "lock_enter",
            "db_enter",
            "circuit_get",
            "db_exit",
            "update",
            "lock_exit",
        ]

    @pytest.fixture
    def patch_circuit_get_not_found(
        self,
        operation_order: list[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        async def _raise_not_found(
            _session: object,
            _circuit_id: UUID,
            **_kwargs: object,
        ) -> object:
            operation_order.append("circuit_get_not_found")
            raise ObjectNotFound(object_name="Circuit")

        monkeypatch.setattr(Circuit, "get", _raise_not_found)

    async def test_deleted_circuit_skips_propagation(
        self,
        health_check_engine: HealthCheckEngine,
        operation_order: list[str],
        patch_circuit_get_not_found: None,
    ) -> None:
        # Act
        await health_check_engine.propagate_route_updates_to_workers(
            cast(Any, SimpleNamespace(id=uuid4())),
            [],
        )

        # Assert - lock acquired, DB read raises ObjectNotFound, early return without update
        # Lock cleanup is handled by unload_circuits, not here
        assert operation_order == [
            "lock_enter",
            "db_enter",
            "circuit_get_not_found",
            "db_exit",
            "lock_exit",
        ]
