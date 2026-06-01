from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import patch

import pytest

from ai.backend.agent.errors.resources import PortPoolExhaustedError
from ai.backend.agent.port_pool import PortPool


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
