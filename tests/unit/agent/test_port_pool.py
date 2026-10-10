from __future__ import annotations

import asyncio
import threading
import uuid
from collections.abc import Iterable, Iterator
from typing import Any, cast, override
from unittest.mock import AsyncMock, patch

import psutil
import pytest

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.errors.resources import PortPoolExhaustedError
from ai.backend.agent.port_pool import PortPool
from ai.backend.agent.types import Container, Port
from ai.backend.common.docker import LabelName
from ai.backend.common.types import ContainerId, ContainerStatus, KernelId


@pytest.fixture
def fake_clock() -> Iterator[list[float]]:
    """Replace ``monotonic`` inside port_pool with a controllable clock.

    The list holds a single mutable ``now`` value; tests advance time by
    overwriting it.
    """
    now = [1000.0]

    def _now() -> float:
        return now[0]

    with patch("ai.backend.agent.port_pool.monotonic", _now):
        yield now


class TestAcquireOrdering:
    def test_initial_ports_are_returned_in_range_order(self) -> None:
        pool = PortPool((30000, 30002), cooldown_sec=60)
        assert [pool.acquire() for _ in range(3)] == [30000, 30001, 30002]

    def test_released_port_is_pushed_to_tail(self, fake_clock: list[float]) -> None:
        pool = PortPool((30000, 30002), cooldown_sec=0)
        first = pool.acquire()
        second = pool.acquire()
        pool.release(first)
        # cooldown_sec=0 disables waiting; first should be at the tail now,
        # so acquire() returns the remaining 30002 before circling back.
        third = pool.acquire()
        assert third == 30002
        fourth = pool.acquire()
        assert fourth == first
        assert second == 30001

    def test_release_refreshes_position_for_already_pooled_port(
        self, fake_clock: list[float]
    ) -> None:
        pool = PortPool((30000, 30002), cooldown_sec=0)
        # Releasing a port that was never acquired still moves it to the tail.
        pool.release(30000)
        assert pool.acquire() == 30001
        assert pool.acquire() == 30002
        assert pool.acquire() == 30000


class TestCooldown:
    def test_release_then_acquire_within_cooldown_raises(self, fake_clock: list[float]) -> None:
        pool = PortPool((30000, 30000), cooldown_sec=60)
        port = pool.acquire()
        pool.release(port)
        # Still within cooldown.
        with pytest.raises(PortPoolExhaustedError):
            pool.acquire()

    def test_acquire_succeeds_after_cooldown_elapses(self, fake_clock: list[float]) -> None:
        pool = PortPool((30000, 30000), cooldown_sec=60)
        port = pool.acquire()
        pool.release(port)
        fake_clock[0] += 60.0
        assert pool.acquire() == port

    def test_respect_cooldown_false_bypasses_wait(self, fake_clock: list[float]) -> None:
        pool = PortPool((30000, 30000), cooldown_sec=60)
        port = pool.acquire()
        pool.release(port)
        # RPC path: cooldown bypassed.
        assert pool.acquire(respect_cooldown=False) == port

    def test_cooldown_zero_disables_waiting(self, fake_clock: list[float]) -> None:
        pool = PortPool((30000, 30000), cooldown_sec=0)
        port = pool.acquire()
        pool.release(port)
        assert pool.acquire() == port

    def test_initial_unused_ports_bypass_cooldown(self, fake_clock: list[float]) -> None:
        # Ports that were never acquired hold released_at=0.0 and should be
        # immediately available even with a non-zero cooldown.
        pool = PortPool((30000, 30002), cooldown_sec=60)
        assert pool.acquire() == 30000
        assert pool.acquire() == 30001


class TestPoolExhaustion:
    def test_empty_pool_raises(self) -> None:
        pool = PortPool((30000, 30000), cooldown_sec=0)
        pool.acquire()
        with pytest.raises(PortPoolExhaustedError):
            pool.acquire()

    def test_invalid_port_range_raises(self) -> None:
        with pytest.raises(ValueError):
            PortPool((30001, 30000), cooldown_sec=0)


class TestReleaseEdgeCases:
    def test_release_out_of_range_is_ignored(self, fake_clock: list[float]) -> None:
        pool = PortPool((30000, 30002), cooldown_sec=0)
        pool.release(29999)
        pool.release(40000)
        assert len(pool) == 3
        assert 29999 not in pool
        assert 40000 not in pool

    def test_release_many_releases_each_in_order(self, fake_clock: list[float]) -> None:
        pool = PortPool((30000, 30002), cooldown_sec=0)
        a = pool.acquire()
        b = pool.acquire()
        c = pool.acquire()
        pool.release_many([b, a, c])
        # release_many releases in iteration order, so b is oldest, then a, then c.
        assert pool.acquire() == b
        assert pool.acquire() == a
        assert pool.acquire() == c


class TestDiscard:
    def test_discard_removes_port_from_pool(self) -> None:
        pool = PortPool((30000, 30002), cooldown_sec=0)
        pool.discard(30001)
        assert 30001 not in pool
        assert pool.acquire() == 30000
        assert pool.acquire() == 30002

    def test_discard_unknown_port_is_noop(self) -> None:
        pool = PortPool((30000, 30002), cooldown_sec=0)
        pool.discard(40000)
        assert len(pool) == 3


class TestUsedPorts:
    def test_used_ports_reports_allocated(self) -> None:
        pool = PortPool((30000, 30002), cooldown_sec=0)
        a = pool.acquire()
        b = pool.acquire()
        assert pool.used_ports() == {a, b}

    def test_used_ports_excludes_released(self, fake_clock: list[float]) -> None:
        pool = PortPool((30000, 30002), cooldown_sec=0)
        a = pool.acquire()
        pool.release(a)
        assert pool.used_ports() == set()


class TestRemaining:
    def test_remaining_reflects_allocation_order(self, fake_clock: list[float]) -> None:
        pool = PortPool((30000, 30002), cooldown_sec=0)
        assert pool.remaining() == [30000, 30001, 30002]
        first = pool.acquire()
        pool.release(first)
        assert pool.remaining() == [30001, 30002, first]


class TestDefer:
    """A fresh pool marks every port never-used, so after a restart the cooldown applied to none.

    `defer` puts it back on ports the host still holds, without claiming them.
    """

    def test_a_deferred_port_is_not_handed_out_within_the_cooldown(
        self, fake_clock: list[float]
    ) -> None:
        pool = PortPool((30000, 30000), cooldown_sec=60)
        pool.defer(30000)
        with pytest.raises(PortPoolExhaustedError):
            pool.acquire()

    def test_it_comes_back_once_the_cooldown_passes(self, fake_clock: list[float]) -> None:
        pool = PortPool((30000, 30000), cooldown_sec=60)
        pool.defer(30000)
        fake_clock[0] += 60.0
        assert pool.acquire() == 30000

    def test_a_free_port_is_still_served_immediately(self, fake_clock: list[float]) -> None:
        pool = PortPool((30000, 30002), cooldown_sec=60)
        pool.defer(30000)
        assert pool.acquire() == 30001

    def test_deferred_ports_go_behind_the_free_ones(self, fake_clock: list[float]) -> None:
        pool = PortPool((30000, 30002), cooldown_sec=60)
        pool.defer_many([30000, 30001])
        assert pool.remaining() == [30002, 30000, 30001]

    def test_a_port_a_live_container_owns_stays_out(self, fake_clock: list[float]) -> None:
        """A `discard`ed port is taken, not cooling down; deferring must not put it back."""
        pool = PortPool((30000, 30002), cooldown_sec=60)
        pool.discard(30001)
        pool.defer(30001)
        assert 30001 not in pool.remaining()

    def test_a_port_outside_the_range_is_ignored(self, fake_clock: list[float]) -> None:
        pool = PortPool((30000, 30002), cooldown_sec=60)
        pool.defer(22)
        assert pool.remaining() == [30000, 30001, 30002]


class _Conn:
    def __init__(self, port: int | None) -> None:
        self.laddr = None if port is None else _Addr(port)


class _Addr:
    def __init__(self, port: int) -> None:
        self.port = port


class _Holder:
    """Only the attribute the method reads; `AbstractAgent` itself cannot be instantiated."""

    def __init__(self, pool: PortPool) -> None:
        self.port_pool = pool

    async def defer_ports_the_host_still_holds(self) -> None:
        await AbstractAgent._defer_ports_the_host_still_holds(cast(Any, self))


class TestDeferPortsTheHostStillHolds:
    async def test_ports_the_host_holds_are_deferred(
        self, fake_clock: list[float], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pool = PortPool((30000, 30002), cooldown_sec=60)
        monkeypatch.setattr(psutil, "net_connections", lambda kind="tcp": [_Conn(30000), _Conn(22)])
        await _Holder(pool).defer_ports_the_host_still_holds()
        assert pool.remaining() == [30001, 30002, 30000]

    async def test_a_port_a_live_kernel_already_claimed_is_not_put_back(
        self, fake_clock: list[float], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pool = PortPool((30000, 30002), cooldown_sec=60)
        pool.discard(30000)  # what the container scan does for our own live kernels
        monkeypatch.setattr(psutil, "net_connections", lambda kind="tcp": [_Conn(30000)])
        await _Holder(pool).defer_ports_the_host_still_holds()
        assert 30000 not in pool.remaining()

    async def test_unreadable_host_sockets_do_not_stop_the_agent(
        self, fake_clock: list[float], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _refuse(kind: str = "tcp") -> list[_Conn]:
            raise psutil.AccessDenied()

        pool = PortPool((30000, 30002), cooldown_sec=60)
        monkeypatch.setattr(psutil, "net_connections", _refuse)
        await _Holder(pool).defer_ports_the_host_still_holds()
        assert pool.remaining() == [30000, 30001, 30002]

    async def test_a_connection_without_a_local_address_is_skipped(
        self, fake_clock: list[float], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pool = PortPool((30000, 30000), cooldown_sec=60)
        monkeypatch.setattr(psutil, "net_connections", lambda kind="tcp": [_Conn(None)])
        await _Holder(pool).defer_ports_the_host_still_holds()
        assert pool.acquire() == 30000

    async def test_the_socket_scan_runs_off_the_event_loop_thread(
        self, fake_clock: list[float], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`psutil.net_connections` blocks; calling it on the loop would stall the agent."""
        scan_threads: list[int] = []

        def _scan(kind: str = "tcp") -> list[_Conn]:
            scan_threads.append(threading.get_ident())
            return []

        monkeypatch.setattr(psutil, "net_connections", _scan)
        await _Holder(PortPool((30000, 30000), cooldown_sec=60)).defer_ports_the_host_still_holds()
        assert scan_threads and scan_threads[0] != threading.get_ident()


class _RecordingPool(PortPool):
    calls: list[tuple[str, int]]

    def __init__(self, port_range: tuple[int, int], cooldown_sec: float) -> None:
        super().__init__(port_range, cooldown_sec=cooldown_sec)
        self.calls = []

    @override
    def discard(self, port: int) -> None:
        self.calls.append(("discard", port))
        super().discard(port)

    @override
    def defer_many(self, ports: Iterable[int]) -> None:
        ports = list(ports)
        self.calls.extend(("defer", p) for p in ports)
        super().defer_many(ports)


class _ScanningAgent:
    """Only the attributes `scan_running_kernels` reads, with no recovered registry or devices."""

    port_pool: PortPool

    def __init__(self, pool: PortPool, containers: list[tuple[KernelId, Container]]) -> None:
        self.port_pool = pool
        self.registry_lock = asyncio.Lock()
        self.resource_lock = asyncio.Lock()
        self.computers: dict[str, Any] = {}
        self._load_kernel_registry_from_recovery = AsyncMock(return_value={})
        self.enumerate_containers = AsyncMock(return_value=containers)
        self.inject_container_lifecycle_event = AsyncMock()

    async def _defer_ports_the_host_still_holds(self) -> None:
        await AbstractAgent._defer_ports_the_host_still_holds(cast(Any, self))

    async def scan_running_kernels(self) -> None:
        await AbstractAgent.scan_running_kernels(cast(Any, self))


class TestScanRunningKernelsDefersHostPorts:
    async def test_a_live_port_stays_out_and_a_host_held_port_goes_to_the_tail(
        self, fake_clock: list[float], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pool = _RecordingPool((30000, 30002), cooldown_sec=60)
        container = Container(
            id=ContainerId("c-live"),
            status=ContainerStatus.RUNNING,
            image="img",
            labels={LabelName.SESSION_ID: str(uuid.uuid4())},
            ports=[Port(host="0.0.0.0", private_port=2000, host_port=30000)],
            backend_obj=None,
        )
        # The live container's own port shows up in the host sockets too.
        monkeypatch.setattr(
            psutil, "net_connections", lambda kind="tcp": [_Conn(30000), _Conn(30001)]
        )
        await _ScanningAgent(pool, [(KernelId(uuid.uuid4()), container)]).scan_running_kernels()

        assert pool.remaining() == [30002, 30001]
        assert pool.calls == [("discard", 30000), ("defer", 30001)]
