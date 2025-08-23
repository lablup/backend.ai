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
class EventTaskArgs:
    """Arguments for creating an EventTask."""

    name: str
    event_factory: Callable[[], AbstractAnycastEvent]
    interval: float
    initial_delay: float = 0.0


class EventTask(PeriodicTask):
    """Periodic task that produces events via EventProducer."""

    _args: Final[EventTaskArgs]
    _event_producer: Final[EventProducer]

    def __init__(
        self,
        args: EventTaskArgs,
        event_producer: EventProducer,
    ) -> None:
        """
        Initialize the event task.

        Args:
            args: Event task arguments
            event_producer: Event producer for sending events
        """
        self._args = args
        self._event_producer = event_producer

    async def run(self) -> None:
        """Execute the task - produce an event."""
        try:
            event = self._args.event_factory()
            await self._event_producer.anycast_event(event)
            log.debug(f"Event task {self._args.name} produced event")
        except Exception:
            log.exception(f"Failed to produce event for task {self._args.name}")

    @property
    def name(self) -> str:
        """Task name."""
        return self._args.name

    @property
    def interval(self) -> float:
        """Interval between task executions."""
        return self._args.interval

    @property
    def initial_delay(self) -> float:
        """Initial delay before first execution."""
        return self._args.initial_delay
