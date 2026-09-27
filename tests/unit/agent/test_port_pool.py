from __future__ import annotations

import inspect
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import psutil
import pytest

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.errors.resources import PortPoolExhaustedError
from ai.backend.agent.port_pool import PortPool, ephemeral_overlap


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


class TestHoldingBackWhatTheHostStillHas:
    """A fresh pool has no memory: every port starts marked never-used, so the cooldown that
    exists to keep a just-released port out of circulation does not apply to any of them. A
    restarted agent therefore hands out ports the host has not let go -- a departing container's
    docker-proxy, a socket in TIME_WAIT -- and the container's bind fails with EADDRINUSE.
    Measured on a restarted node: 9 of 12 sessions failed that way, against 3 of 12 once the same
    node had settled.
    """

    def test_a_fresh_pool_would_hand_out_every_port_at_once(self) -> None:
        """The state the fix is against, pinned so the reason for it stays visible."""
        pool = PortPool((30000, 30002), cooldown_sec=60)
        assert [pool.acquire() for _ in range(3)] == [30000, 30001, 30002]

    def test_a_deferred_port_is_not_handed_out_within_the_cooldown(
        self, fake_clock: list[float]
    ) -> None:
        pool = PortPool((30000, 30000), cooldown_sec=60)
        pool.defer(30000)
        with pytest.raises(PortPoolExhaustedError):
            pool.acquire()

    def test_it_comes_back_once_the_cooldown_passes(self, fake_clock: list[float]) -> None:
        """Held back, not taken away: the host will let the port go, and the pool is small."""
        pool = PortPool((30000, 30000), cooldown_sec=60)
        pool.defer(30000)
        fake_clock[0] += 60.0
        assert pool.acquire() == 30000

    def test_a_free_port_is_still_served_immediately(self, fake_clock: list[float]) -> None:
        """Deferring must not stall a restart: only the ports the host holds wait."""
        pool = PortPool((30000, 30002), cooldown_sec=60)
        pool.defer(30000)
        assert pool.acquire() == 30001

    def test_deferred_ports_go_behind_the_free_ones(self, fake_clock: list[float]) -> None:
        pool = PortPool((30000, 30002), cooldown_sec=60)
        pool.defer_many([30000, 30001])
        assert pool.remaining() == [30002, 30000, 30001]

    def test_a_port_a_live_container_owns_stays_out(self, fake_clock: list[float]) -> None:
        """`discard` and `defer` answer different questions. A live kernel's port is not waiting
        for a cooldown -- it is taken -- and deferring it would put it back in the queue for the
        next session to bind over."""
        pool = PortPool((30000, 30002), cooldown_sec=60)
        pool.discard(30001)
        pool.defer(30001)
        assert 30001 not in pool.remaining()

    def test_a_port_outside_the_range_is_ignored(self, fake_clock: list[float]) -> None:
        """The host's sockets are scanned node-wide; most of what comes back is not ours."""
        pool = PortPool((30000, 30002), cooldown_sec=60)
        pool.defer(22)
        assert pool.remaining() == [30000, 30001, 30002]


class _Conn:
    def __init__(self, port: int | None) -> None:
        self.laddr = None if port is None else _Addr(port)


class _Addr:
    def __init__(self, port: int) -> None:
        self.port = port


class TestTheStartupScanIsWiredIn:
    """The pool method above is only worth having if startup calls it. `scan_running_kernels`
    `discard`s the ports our own live kernels hold; everything the host holds beyond those is what
    this defers."""

    class _Holder:
        """Only the attribute the method reads. `AbstractAgent` cannot be instantiated -- it has
        eighteen abstract methods -- and the method under test is the shipped one either way."""

        def __init__(self, pool: PortPool) -> None:
            self.port_pool = pool

        def _defer_ports_the_host_still_holds(self) -> None:
            AbstractAgent._defer_ports_the_host_still_holds(cast(Any, self))

    def _agent_with(self, pool: PortPool) -> _Holder:
        return self._Holder(pool)

    def test_ports_the_host_holds_are_deferred(
        self, fake_clock: list[float], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pool = PortPool((30000, 30002), cooldown_sec=60)
        monkeypatch.setattr(psutil, "net_connections", lambda kind="tcp": [_Conn(30000), _Conn(22)])
        self._agent_with(pool)._defer_ports_the_host_still_holds()
        assert pool.remaining() == [30001, 30002, 30000], (
            "the port the host still holds was left at the head, so the next session binds over it"
        )

    def test_a_port_a_live_kernel_already_claimed_is_not_put_back(
        self, fake_clock: list[float], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pool = PortPool((30000, 30002), cooldown_sec=60)
        pool.discard(30000)  # what the container scan does for our own live kernels
        monkeypatch.setattr(psutil, "net_connections", lambda kind="tcp": [_Conn(30000)])
        self._agent_with(pool)._defer_ports_the_host_still_holds()
        assert 30000 not in pool.remaining()

    def test_a_host_that_will_not_say_does_not_stop_the_agent(
        self, fake_clock: list[float], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Reading the host's sockets can be refused. A node that cannot is no worse off than
        before this existed, so it carries on rather than refusing to start."""

        def _refuse(kind: str = "tcp") -> list[_Conn]:
            raise psutil.AccessDenied()

        pool = PortPool((30000, 30002), cooldown_sec=60)
        monkeypatch.setattr(psutil, "net_connections", _refuse)
        self._agent_with(pool)._defer_ports_the_host_still_holds()
        assert pool.remaining() == [30000, 30001, 30002]

    def test_a_connection_without_a_local_address_is_skipped(
        self, fake_clock: list[float], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pool = PortPool((30000, 30000), cooldown_sec=60)
        monkeypatch.setattr(psutil, "net_connections", lambda kind="tcp": [_Conn(None)])
        self._agent_with(pool)._defer_ports_the_host_still_holds()
        assert pool.acquire() == 30000

    def test_startup_calls_it_after_claiming_our_own_kernels_ports(self) -> None:
        """Order is the invariant, not just presence. `scan_running_kernels` `discard`s the ports
        our live kernels hold; deferring before that would put those back in the queue with a
        cooldown, and the next session would bind over a running kernel."""
        source = inspect.getsource(AbstractAgent.scan_running_kernels)
        assert "_defer_ports_the_host_still_holds()" in source, (
            "startup no longer holds back the ports the host still has, so the first sessions"
            " after a restart bind against them and fail with EADDRINUSE"
        )
        assert source.index("port_pool.discard(") < source.index(
            "_defer_ports_the_host_still_holds()"
        ), "the host scan must come after our own kernels' ports are claimed"


class TestThePoolRangeAgainstTheKernelsEphemeralRange:
    """The failure this exists to name. A published host port is bound by docker-proxy when the
    kernel starts; if the same number is inside `ip_local_port_range` and not reserved, the kernel
    may already have given it to some process as the SOURCE port of an outgoing connection, and
    the bind fails with EADDRINUSE. Measured on a live node: dockerd held 33220 that way for nine
    minutes while the pool's range was 33100-33600, and a dozen more sat in TIME_WAIT.

    Nothing in the pool is wrong when it happens -- it never handed the port out twice -- so
    without this the only symptom is a session that fails to start and a next one that does not.
    """

    @staticmethod
    def _settings(tmp_path: Path, rng: str, reserved: str) -> tuple[Path, Path]:
        (tmp_path / "range").write_text(rng)
        (tmp_path / "reserved").write_text(reserved)
        return tmp_path / "range", tmp_path / "reserved"

    def test_an_unreserved_range_inside_the_ephemeral_one_is_reported(self, tmp_path: Path) -> None:
        r, res = self._settings(tmp_path, "32768\t60999\n", "\n")
        assert ephemeral_overlap((33100, 33600), range_path=r, reserved_path=res) == (33100, 33600)

    def test_reserving_the_whole_range_clears_it(self, tmp_path: Path) -> None:
        r, res = self._settings(tmp_path, "32768\t60999\n", "33100-33600")
        assert ephemeral_overlap((33100, 33600), range_path=r, reserved_path=res) is None

    def test_only_the_part_left_exposed_is_reported(self, tmp_path: Path) -> None:
        """A half-done reservation is the shape an operator most easily leaves behind."""
        r, res = self._settings(tmp_path, "32768\t60999\n", "33100-33500")
        assert ephemeral_overlap((33100, 33600), range_path=r, reserved_path=res) == (33501, 33600)

    def test_a_range_below_the_ephemeral_one_is_not_reported(self, tmp_path: Path) -> None:
        r, res = self._settings(tmp_path, "32768\t60999\n", "\n")
        assert ephemeral_overlap((20000, 21000), range_path=r, reserved_path=res) is None

    def test_settings_that_cannot_be_read_are_not_a_refusal(self, tmp_path: Path) -> None:
        """A node that cannot be asked is not a node to hold back; this only ever warns."""
        missing = tmp_path / "nope"
        assert ephemeral_overlap((33100, 33600), range_path=missing, reserved_path=missing) is None

    def test_singles_and_ranges_both_parse(self, tmp_path: Path) -> None:
        r, res = self._settings(tmp_path, "32768\t60999\n", "33100,33102-33104,33600")
        assert ephemeral_overlap((33100, 33104), range_path=r, reserved_path=res) == (33101, 33101)

    def test_startup_says_so(self) -> None:
        """Wired into the agent, not merely available: the whole value is that it is said once at
        startup instead of discovered from an intermittent EADDRINUSE hours later."""
        source = inspect.getsource(AbstractAgent.__init__)
        assert "ephemeral_overlap(" in source
