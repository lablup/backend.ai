"""Generic healthy-endpoint pool for HTTP upstream services.

The pool's responsibility is narrow: keep the set of *healthy* endpoints
accurate, hand one out per call, and record caller request outcomes so the
next ``acquire`` skips a dying endpoint. Per-user HTTP client sessions
(cookies, access keys, etc.) are NOT this pool's concern — those live in
the user-scoped ``ClientPool`` consumed downstream.

What this pool does:

1. Holds one **probe-only** ``aiohttp.ClientSession`` per configured
   endpoint, created eagerly at startup via the caller-provided
   ``probe_session_factory``. The session is used solely for the background
   readiness probe; it is not exposed to callers and is never closed on
   health transitions — only when :meth:`close` is awaited — so probe
   recovery is a zero-cost flag flip.
2. Runs a periodic ``GET <probe_path>`` per endpoint. Consecutive failures
   past ``EndpointPoolSpec.failure_threshold`` flip the endpoint to
   unhealthy; the next probe success (or successful caller request)
   restores it.
3. Delegates "which healthy endpoint to use" to an
   :class:`EndpointSelectionStrategy` passed in at construction time.
4. Owns the bookkeeping for caller request outcomes. The acquire context
   itself records connection-level failures (so the next select skips a
   dying endpoint) and records success on clean exit (so the failure
   counter resets on recovery). Business-level exceptions (e.g. HTTP 4xx
   surfacing as application errors) are *not* counted, since they ride on
   top of a working connection.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass

import aiohttp
from aiotools import cancel_and_wait

from ai.backend.logging import BraceStyleAdapter
from ai.backend.web.errors import ManagerConnectionUnavailable

from .strategy import EndpointSelectionStrategy
from .types import AcquiredEndpoint, EndpointEntry, EndpointPoolSpec

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Caller-side exceptions that signal an unreachable / unhealthy endpoint as
# opposed to a business error riding on a working connection. The acquire
# context counts these against the endpoint before re-raising.
_CONNECTION_ERRORS: tuple[type[BaseException], ...] = (
    aiohttp.ClientConnectionError,
    TimeoutError,
    ConnectionError,
    OSError,
)


@dataclass
class _CachedEntry:
    """Per-endpoint state.

    The ``entry`` view is what gets handed to the selection strategy; the
    rest is internal bookkeeping the strategy does not see. ``probe_session``
    is used by the background probe loop only and is never exposed
    externally.
    """

    entry: EndpointEntry
    probe_session: aiohttp.ClientSession
    is_healthy: bool = True
    failure_count: int = 0
    unhealthy_since: float | None = None


class HealthyEndpointPool:
    _entries: dict[str, _CachedEntry]
    _spec: EndpointPoolSpec
    _strategy: EndpointSelectionStrategy
    _lock: asyncio.Lock
    _health_check_task: asyncio.Task[None]

    def __init__(
        self,
        *,
        endpoints: Sequence[str],
        spec: EndpointPoolSpec,
        strategy: EndpointSelectionStrategy,
        probe_session_factory: Callable[[str], aiohttp.ClientSession],
    ) -> None:
        self._spec = spec
        self._strategy = strategy
        self._entries = {
            endpoint: _CachedEntry(
                entry=EndpointEntry(endpoint=endpoint),
                probe_session=probe_session_factory(endpoint),
            )
            for endpoint in endpoints
        }
        self._lock = asyncio.Lock()
        self._health_check_task = asyncio.create_task(
            self._health_check_loop(),
            name="HealthyEndpointPool._health_check_loop",
        )

    async def close(self) -> None:
        await cancel_and_wait(self._health_check_task)
        await asyncio.gather(
            *(cached.probe_session.close() for cached in self._entries.values()),
            return_exceptions=True,
        )

    # --- Acquisition ----------------------------------------------------

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[AcquiredEndpoint]:
        """Yield a healthy endpoint chosen by the configured strategy.

        On context exit, a caller exception matching ``_CONNECTION_ERRORS``
        is recorded against the chosen endpoint and re-raised; a clean exit
        resets that endpoint's failure counter (so a single success after
        intermittent probe failures restores it).

        Raises :class:`ManagerConnectionUnavailable` when no endpoint is
        currently healthy.
        """
        async with self._lock:
            healthy_entries = [
                cached.entry for cached in self._entries.values() if cached.is_healthy
            ]
        if not healthy_entries:
            raise ManagerConnectionUnavailable(
                "no healthy endpoint is available",
            )
        async with self._strategy.acquire(healthy_entries) as chosen_entry:
            cached = self._entries[chosen_entry.endpoint]
            async with self._record_outcome(cached):
                yield AcquiredEndpoint(endpoint=cached.entry.endpoint)

    @asynccontextmanager
    async def acquire_sticky(self, endpoint: str) -> AsyncIterator[AcquiredEndpoint]:
        """Yield the given endpoint if healthy, otherwise raise 503.

        Routed through ``strategy.acquire`` with a single-entry sequence so
        that stateful strategies (e.g. LeastConnections) still see the
        acquire/release pair and keep their counters consistent. Outcome
        recording follows the same rules as :meth:`acquire`.
        """
        cached = self._entries.get(endpoint)
        if cached is None or not cached.is_healthy:
            raise ManagerConnectionUnavailable(
                f"endpoint {endpoint!r} is not healthy",
            )
        async with self._strategy.acquire([cached.entry]) as chosen_entry:
            target = self._entries[chosen_entry.endpoint]
            async with self._record_outcome(target):
                yield AcquiredEndpoint(endpoint=target.entry.endpoint)

    @asynccontextmanager
    async def _record_outcome(self, cached: _CachedEntry) -> AsyncIterator[None]:
        try:
            yield
        except _CONNECTION_ERRORS as error:
            self._mark_failure(cached, reason=f"request: {error}")
            raise
        else:
            self._mark_success(cached)

    # --- Health-state read API -----------------------------------------

    def is_healthy(self, endpoint: str) -> bool:
        cached = self._entries.get(endpoint)
        return cached is not None and cached.is_healthy

    def has_any_healthy(self) -> bool:
        return any(cached.is_healthy for cached in self._entries.values())

    def healthy_endpoints(self) -> list[str]:
        return [endpoint for endpoint, cached in self._entries.items() if cached.is_healthy]

    def all_endpoints(self) -> list[str]:
        return list(self._entries.keys())

    # --- Internal bookkeeping ------------------------------------------

    def _mark_failure(self, cached: _CachedEntry, *, reason: str) -> None:
        cached.failure_count += 1
        if self._spec.is_failure_threshold_reached(cached.failure_count) and cached.is_healthy:
            cached.is_healthy = False
            cached.unhealthy_since = time.perf_counter()
            log.info(
                "Endpoint {} marked unhealthy ({}): failures={}",
                cached.entry.endpoint,
                reason,
                cached.failure_count,
            )

    def _mark_success(self, cached: _CachedEntry) -> None:
        was_unhealthy = not cached.is_healthy
        cached.is_healthy = True
        cached.failure_count = 0
        cached.unhealthy_since = None
        if was_unhealthy:
            log.info("Endpoint {} recovered", cached.entry.endpoint)

    # --- Background probe loop -----------------------------------------

    async def _health_check_loop(self) -> None:
        while True:
            await asyncio.sleep(self._spec.health_check_interval)
            await self._check_all_health()

    async def _check_all_health(self) -> None:
        if not self._entries:
            return
        await asyncio.gather(
            *(self._check_one_health(cached) for cached in self._entries.values()),
            return_exceptions=True,
        )

    async def _check_one_health(self, cached: _CachedEntry) -> None:
        try:
            async with asyncio.timeout(self._spec.probe_timeout):
                async with cached.probe_session.get(self._spec.probe_path) as resp:
                    # Only 2xx is treated as a healthy probe. 4xx (path
                    # missing, auth-required surface) is a failure because
                    # we cannot distinguish "endpoint up but wrong path"
                    # from "endpoint half-broken" without the upstream
                    # exposing a real readiness route. Once every server's
                    # public API exposes a status-only /readyz the probe
                    # becomes a clean signal.
                    if not (200 <= resp.status < 300):
                        raise ConnectionError(f"probe HTTP {resp.status}")
        except Exception as error:
            self._mark_failure(cached, reason=f"probe: {error}")
            return
        self._mark_success(cached)
