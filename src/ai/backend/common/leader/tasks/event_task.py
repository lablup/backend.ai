"""Event task implementation for producing events via EventProducer."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Final

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.types import AbstractAnycastEvent
from ai.backend.common.leader.tasks.base import PeriodicTask
from ai.backend.common.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass(frozen=True)
class EventTaskSpec:
    """Specification for an event-based periodic task."""

    name: str
    event_factory: Callable[[], AbstractAnycastEvent]
    interval: float
    initial_delay: float = 0.0


class EventProducerTask(PeriodicTask):
    """Periodic task that produces events via EventProducer."""

    _spec: Final[EventTaskSpec]
    _event_producer: Final[EventProducer]

    def __init__(
        self,
        spec: EventTaskSpec,
        event_producer: EventProducer,
    ) -> None:
        """
        Initialize the event producer task.

        Args:
            spec: Event task specification
            event_producer: Event producer for sending events
        """
        self._spec = spec
        self._event_producer = event_producer

    async def run(self) -> None:
        """Execute the task - produce an event."""
        try:
            event = self._spec.event_factory()
            await self._event_producer.anycast_event(event)
            log.debug(f"Event task {self._spec.name} produced event")
        except Exception:
            log.exception(f"Failed to produce event for task {self._spec.name}")

    @property
    def name(self) -> str:
        """Task name."""
        return self._spec.name

    @property
    def interval(self) -> float:
        """Interval between task executions."""
        return self._spec.interval

    @property
    def initial_delay(self) -> float:
        """Initial delay before first execution."""
        return self._spec.initial_delay
