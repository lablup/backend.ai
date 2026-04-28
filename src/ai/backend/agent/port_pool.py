"""
Host port allocator for the agent.

This module provides :class:`PortPool`, a FIFO queue with per-port reuse
cooldown. It replaces the previous ``set[int]`` + ``set.pop()`` pattern
which was non-deterministic and could re-allocate a port immediately
after release, conflicting with TCP TIME_WAIT and stale firewall or
monitoring state.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable
from time import monotonic

from ai.backend.agent.errors.resources import PortPoolExhaustedError

__all__ = ("PortPool",)


class PortPool:
    """Host port allocator with FIFO ordering and time-based reuse cooldown.

    Released ports are pushed to the end of the queue and excluded from
    re-allocation until ``cooldown_sec`` has elapsed. The oldest port
    (either never used or longest released) is always allocated first.
    """

    _ports: OrderedDict[int, float]
    _start: int
    _end: int
    _cooldown_sec: float

    def __init__(self, port_range: tuple[int, int], cooldown_sec: float) -> None:
        start, end = port_range
        if start > end:
            raise ValueError(f"invalid port_range: start={start} > end={end}")
        self._start = start
        self._end = end
        self._cooldown_sec = cooldown_sec
        # Initial unused ports get released_at=0.0 so they always pass cooldown.
        self._ports = OrderedDict.fromkeys(range(start, end + 1), 0.0)

    def __len__(self) -> int:
        return len(self._ports)

    def __contains__(self, port: object) -> bool:
        return port in self._ports

    def acquire(self, *, respect_cooldown: bool = True) -> int:
        """Allocate the oldest available port.

        Raises :class:`PortPoolExhaustedError` when the pool is empty or,
        if ``respect_cooldown`` is True, when the oldest port is still
        within its cooldown window.
        """
        if not self._ports:
            raise PortPoolExhaustedError("no host ports available in pool")
        port, released_at = next(iter(self._ports.items()))
        if respect_cooldown and self._cooldown_sec > 0:
            elapsed = monotonic() - released_at
            if elapsed < self._cooldown_sec:
                raise PortPoolExhaustedError(
                    f"all available host ports are in cooldown "
                    f"(oldest released {elapsed:.1f}s ago, "
                    f"cooldown={self._cooldown_sec}s)"
                )
        del self._ports[port]
        return port

    def release(self, port: int) -> None:
        """Return a port to the pool, marking it as just released.

        The port is moved to the tail of the queue and its release
        timestamp is refreshed. Out-of-range ports are silently ignored,
        which matches the prior ``_restore_ports`` behavior when the
        agent restarts with a different ``port_range``.
        """
        if not (self._start <= port <= self._end):
            return
        self._ports.pop(port, None)
        self._ports[port] = monotonic()

    def release_many(self, ports: Iterable[int]) -> None:
        """Release multiple ports at once. See :meth:`release`."""
        for p in ports:
            self.release(p)

    def discard(self, port: int) -> None:
        """Remove a port from the pool without scheduling reuse.

        Used during startup scans when an existing container is found to
        already occupy a port; that port should not appear in the pool
        until the container is gone.
        """
        self._ports.pop(port, None)

    def used_ports(self) -> set[int]:
        """Return the set of ports currently allocated (not in the pool)."""
        return set(range(self._start, self._end + 1)) - self._ports.keys()

    def remaining(self) -> list[int]:
        """Return ports currently in the pool, in FIFO (allocation) order."""
        return list(self._ports.keys())
