from __future__ import annotations

import asyncio
import contextlib
import logging
import random
import time
from dataclasses import dataclass

from ai.backend.appproxy.common.errors import WorkerNotAvailable
from ai.backend.appproxy.common.types import RouteInfo
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass(slots=True)
class _PoolEntry:
    """Per-endpoint health/state entry keyed by ``(host, port)``.

    ``route`` carries the currently cached :class:`RouteInfo` for this
    endpoint; when a route update arrives with the same ``(host, port)``
    but a different ``route_id`` we treat it as a fresh kernel and reset
    the entry, avoiding false-positive unhealthy carry-over from a
    previously terminated kernel on the same host/port.
    """

    route: RouteInfo
    is_healthy: bool = True
    failure_count: int = 0
    unhealthy_since: float | None = None


@dataclass(slots=True)
class RoutePoolSpec:
    """Runtime tunables for a per-backend :class:`RoutePool`."""

    failure_threshold: int = 3
    health_check_interval: float = 10.0
    connect_timeout: float = 1.0
    recovery_timeout: float = 60.0


class RoutePool:
    """Per-backend route pool with TCP-reachability health checks.

    Entries are keyed by ``(host, port)``. Selection picks a healthy
    entry via ``traffic_ratio``-weighted random. TCP connect probes run
    in the background and flip entries between healthy / unhealthy;
    after ``recovery_timeout`` without recovery the entry is evicted.

    Manager-issued route updates are applied via :meth:`update`:

    - ``(host, port)`` newly present → insert a fresh entry
    - ``(host, port)`` missing from the update → drop the entry
    - ``(host, port)`` present with a different ``route_id`` → treated
      as a kernel swap: reset to a fresh entry (prior health state is
      assumed stale and must not leak into the new kernel)
    - ``(host, port)`` present with the same ``route_id`` → update only
      the cached route metadata (``traffic_ratio`` etc.)
    """

    _entries: dict[tuple[str, int], _PoolEntry]
    _lock: asyncio.Lock
    _health_check_task: asyncio.Task[None] | None
    _spec: RoutePoolSpec

    def __init__(
        self,
        initial_routes: list[RouteInfo] | None = None,
        *,
        spec: RoutePoolSpec | None = None,
    ) -> None:
        self._entries = {}
        self._lock = asyncio.Lock()
        self._spec = spec or RoutePoolSpec()
        if initial_routes:
            for r in initial_routes:
                self._entries[(r.current_kernel_host, r.kernel_port)] = _PoolEntry(route=r)
        self._health_check_task = asyncio.create_task(
            self._health_check_loop(),
            name="RoutePool._health_check_loop",
        )

    async def close(self) -> None:
        task = self._health_check_task
        if task is not None:
            task.cancel()
            with contextlib.suppress(BaseException):
                await task
            self._health_check_task = None

    async def update(self, new_routes: list[RouteInfo]) -> None:
        async with self._lock:
            new_by_hp: dict[tuple[str, int], RouteInfo] = {
                (r.current_kernel_host, r.kernel_port): r for r in new_routes
            }
            for hp in list(self._entries.keys()):
                if hp not in new_by_hp:
                    del self._entries[hp]
            for hp, new_route in new_by_hp.items():
                existing = self._entries.get(hp)
                if existing is None:
                    self._entries[hp] = _PoolEntry(route=new_route)
                elif existing.route.route_id != new_route.route_id:
                    # Same host:port but route_id changed → treat as kernel
                    # swap; start the new entry from a clean slate so the
                    # old kernel's unhealthy state cannot taint the new one.
                    self._entries[hp] = _PoolEntry(route=new_route)
                else:
                    existing.route = new_route

    async def select(self) -> RouteInfo:
        async with self._lock:
            candidates = [
                entry.route
                for entry in self._entries.values()
                if entry.is_healthy and entry.route.traffic_ratio > 0
            ]
        if not candidates:
            raise WorkerNotAvailable
        if len(candidates) == 1:
            return candidates[0]
        ratios = [r.traffic_ratio for r in candidates]
        return random.choices(candidates, weights=ratios, k=1)[0]

    def record_failure(self, route: RouteInfo) -> None:
        entry = self._entries.get((route.current_kernel_host, route.kernel_port))
        if entry is None or entry.route.route_id != route.route_id:
            return
        entry.failure_count += 1
        if entry.failure_count >= self._spec.failure_threshold:
            entry.is_healthy = False
            if entry.unhealthy_since is None:
                entry.unhealthy_since = time.perf_counter()
            log.debug(
                "Route {}:{} marked unhealthy after {} failures",
                route.current_kernel_host,
                route.kernel_port,
                entry.failure_count,
            )

    def record_success(self, route: RouteInfo) -> None:
        entry = self._entries.get((route.current_kernel_host, route.kernel_port))
        if entry is None or entry.route.route_id != route.route_id:
            return
        entry.failure_count = 0
        entry.is_healthy = True
        entry.unhealthy_since = None

    async def _health_check_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(self._spec.health_check_interval)
                try:
                    await self._check_all()
                except Exception:
                    log.exception("RoutePool health check iteration failed")
        except asyncio.CancelledError:
            raise

    async def _check_all(self) -> None:
        async with self._lock:
            snapshot = list(self._entries.items())
        if not snapshot:
            return
        await asyncio.gather(
            *(self._probe_one(hp, entry) for hp, entry in snapshot),
            return_exceptions=True,
        )

    async def _probe_one(self, hp: tuple[str, int], entry: _PoolEntry) -> None:
        host, port = hp
        ok = await self._tcp_probe(host, port)
        if ok:
            entry.is_healthy = True
            entry.failure_count = 0
            entry.unhealthy_since = None
            return
        entry.is_healthy = False
        if entry.unhealthy_since is None:
            entry.unhealthy_since = time.perf_counter()
        if (
            entry.unhealthy_since is not None
            and time.perf_counter() - entry.unhealthy_since > self._spec.recovery_timeout
        ):
            async with self._lock:
                cached = self._entries.get(hp)
                if cached is not None and cached.route.route_id == entry.route.route_id:
                    del self._entries[hp]
                    log.info(
                        "Evicted unreachable route {}:{} after {}s",
                        host,
                        port,
                        self._spec.recovery_timeout,
                    )

    async def _tcp_probe(self, host: str, port: int) -> bool:
        try:
            _reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host=host, port=port),
                timeout=self._spec.connect_timeout,
            )
        except Exception:
            return False
        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()
        return True


__all__ = (
    "RoutePool",
    "RoutePoolSpec",
)
