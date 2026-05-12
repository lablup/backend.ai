"""Endpoint selection strategies for HTTP endpoint pools.

Each strategy exposes :meth:`acquire` as an async context manager. The pool
opens it with ``async with strategy.acquire(healthy_entries) as entry:`` so
the release path (decrementing an in-flight counter, etc.) is run exactly
once on context exit. Strategies that do not track per-acquisition state
simply yield without any teardown.

Three strategies are provided:

- :class:`RoundRobinStrategy` — rotates with a bounded cursor.
- :class:`RandomStrategy` — uniform random pick.
- :class:`LeastConnectionsStrategy` — selects the endpoint with the fewest
  outstanding acquisitions, tracked across the acquire/release window.

Strategy implementations are not internally synchronized. The pool serializes
``acquire`` entry behind its own lock, so single-event-loop callers see a
consistent view.
"""

from __future__ import annotations

import enum
import random
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import override

from .types import EndpointEntry


class EndpointSelectionPolicy(enum.StrEnum):
    """Configured policy name (1:1 with the strategy implementations)."""

    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_CONNECTIONS = "least_connections"


class EndpointSelectionStrategy(ABC):
    """Picks one entry and yields it inside an async context."""

    @abstractmethod
    def acquire(
        self,
        healthy_entries: Sequence[EndpointEntry],
    ) -> AbstractAsyncContextManager[EndpointEntry]:
        """Return an async context manager that yields the chosen entry.

        The argument must be a non-empty sequence; emptiness is the caller's
        responsibility to rule out before invocation.
        """


class RoundRobinStrategy(EndpointSelectionStrategy):
    """Rotates through the healthy set with a cursor bounded by the healthy length.

    The cursor is reduced modulo the current healthy length immediately after
    each advance, keeping its value in ``[0, len(healthy_entries))`` and
    avoiding any long-running int growth.
    """

    _cursor: int

    def __init__(self) -> None:
        self._cursor = 0

    @override
    @asynccontextmanager
    async def acquire(
        self,
        healthy_entries: Sequence[EndpointEntry],
    ) -> AsyncIterator[EndpointEntry]:
        chosen = healthy_entries[self._cursor % len(healthy_entries)]
        self._cursor = (self._cursor + 1) % len(healthy_entries)
        yield chosen


class RandomStrategy(EndpointSelectionStrategy):
    """Uniform random pick. Stateless."""

    @override
    @asynccontextmanager
    async def acquire(
        self,
        healthy_entries: Sequence[EndpointEntry],
    ) -> AsyncIterator[EndpointEntry]:
        yield random.choice(healthy_entries)


class LeastConnectionsStrategy(EndpointSelectionStrategy):
    """Selects the entry with the fewest outstanding acquisitions.

    Ties are broken by the order entries first appear in the healthy
    sequence passed to :meth:`acquire` (``min`` is stable on equal keys). The
    in-flight counter is incremented on entry and decremented on exit so the
    release path runs even if the caller raises inside the ``async with``.

    The counter is keyed by ``EndpointEntry.endpoint`` (the URL) rather than
    by the entry object so that pool-side entry instances and metadata-only
    snapshots compare consistently.
    """

    _in_flight: dict[str, int]

    def __init__(self) -> None:
        self._in_flight = {}

    @override
    @asynccontextmanager
    async def acquire(
        self,
        healthy_entries: Sequence[EndpointEntry],
    ) -> AsyncIterator[EndpointEntry]:
        chosen = min(
            healthy_entries,
            key=lambda candidate: self._in_flight.get(candidate.endpoint, 0),
        )
        self._in_flight[chosen.endpoint] = self._in_flight.get(chosen.endpoint, 0) + 1
        try:
            yield chosen
        finally:
            current = self._in_flight.get(chosen.endpoint, 0)
            if current <= 1:
                self._in_flight.pop(chosen.endpoint, None)
            else:
                self._in_flight[chosen.endpoint] = current - 1

    def in_flight_count(self, endpoint: str) -> int:
        return self._in_flight.get(endpoint, 0)


def build_endpoint_selection_strategy(
    policy: EndpointSelectionPolicy,
) -> EndpointSelectionStrategy:
    match policy:
        case EndpointSelectionPolicy.ROUND_ROBIN:
            return RoundRobinStrategy()
        case EndpointSelectionPolicy.RANDOM:
            return RandomStrategy()
        case EndpointSelectionPolicy.LEAST_CONNECTIONS:
            return LeastConnectionsStrategy()
