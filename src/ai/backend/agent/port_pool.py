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
from pathlib import Path
from time import monotonic
from typing import Final

from ai.backend.agent.errors.resources import PortPoolExhaustedError

__all__ = ("PortPool", "ephemeral_overlap")


#: Where the kernel is told which ports it may hand out as the SOURCE port of an outgoing
#: connection, and which of those are spoken for.
_EPHEMERAL_RANGE_PATH: Final = Path("/proc/sys/net/ipv4/ip_local_port_range")
_RESERVED_PORTS_PATH: Final = Path("/proc/sys/net/ipv4/ip_local_reserved_ports")


def _parse_reserved(raw: str) -> set[int]:
    """`ip_local_reserved_ports` as a set. Comma-separated singles and `a-b` ranges."""
    reserved: set[int] = set()
    for part in raw.replace(" ", "").split(","):
        if not part:
            continue
        low, _, high = part.partition("-")
        try:
            reserved.update(range(int(low), int(high or low) + 1))
        except ValueError:
            continue
    return reserved


def ephemeral_overlap(
    port_range: tuple[int, int],
    *,
    range_path: Path = _EPHEMERAL_RANGE_PATH,
    reserved_path: Path = _RESERVED_PORTS_PATH,
) -> tuple[int, int] | None:
    """The part of ``port_range`` the kernel may still hand out as an ephemeral source port.

    A published host port is bound by the runtime (docker-proxy) when the kernel starts. If the
    same number is inside ``ip_local_port_range`` and not in ``ip_local_reserved_ports``, the
    kernel is free to give it to any process opening an outgoing connection first -- and the bind
    then fails with EADDRINUSE. Measured on a live node: `dockerd` held 33220 as the source port
    of one connection for nine minutes while the pool's range was 33100-33600, and loopback
    connections sat in TIME_WAIT on a dozen more.

    It reads as a flaky agent. The session that drew the port fails to start, the next one on a
    different port succeeds, and nothing in the pool's own bookkeeping is wrong -- it never handed
    the port out twice.

    None when the ranges do not overlap, or when the settings cannot be read (a node that cannot
    be asked is not a node to refuse).
    """
    try:
        low_s, _, high_s = range_path.read_text().strip().partition("\t")
        eph_low, eph_high = int(low_s), int(high_s or low_s)
    except (OSError, ValueError):
        return None
    lo = max(port_range[0], eph_low)
    hi = min(port_range[1], eph_high)
    if lo > hi:
        return None
    try:
        reserved = _parse_reserved(reserved_path.read_text())
    except OSError:
        reserved = set()
    exposed = [p for p in range(lo, hi + 1) if p not in reserved]
    if not exposed:
        return None
    return exposed[0], exposed[-1]


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

    def defer(self, port: int) -> None:
        """Hold a port back until its cooldown passes, without claiming it.

        For a port the HOST still holds although no live container of ours does: the docker-proxy
        of a container on its way out, or a socket in TIME_WAIT. The pool is built with every port
        marked never-used, so a restarted agent hands those straight out and the container's bind
        fails with EADDRINUSE -- the one moment this cooldown exists for is the one moment it did
        not apply. Measured on a restarted node: 9 of 12 sessions failed that way, against 3 of 12
        once it had settled.

        A port already `discard`ed stays out: a live container owns it, and the cooldown is not
        what is keeping it away.
        """
        if port not in self._ports:
            return
        del self._ports[port]
        self._ports[port] = monotonic()

    def defer_many(self, ports: Iterable[int]) -> None:
        """Hold back multiple ports at once. See :meth:`defer`."""
        for p in ports:
            self.defer(p)

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
