from __future__ import annotations

import asyncio
import logging
import os
import uuid
from typing import TYPE_CHECKING, Callable, Final, Optional

from .events import GlobalTimerCreatedEvent, GlobalTimerJoinEvent, GlobalTimerLeaveEvent
from .logging import BraceStyleAdapter

if TYPE_CHECKING:
    from .events import AbstractEvent, EventDispatcher, EventProducer
    from .lock import AbstractDistributedLock


log = BraceStyleAdapter(logging.getLogger(__name__))


class GlobalTimer:

    """
    Executes the given async function only once in the given interval,
    uniquely among multiple manager instances across multiple nodes.
    """

    _event_producer: Final[EventProducer]

    def __init__(
        self,
        dist_lock: AbstractDistributedLock,
        event_producer: EventProducer,
        event_factory: Callable[[], AbstractEvent],
        interval: float = 10.0,
        initial_delay: float = 0.0,
    ) -> None:
        self._dist_lock = dist_lock
        self._event_producer = event_producer
        self._event_factory = event_factory
        self._stopped = False
        self.interval = interval
        self.initial_delay = initial_delay

    async def generate_tick(self) -> None:
        try:
            await asyncio.sleep(self.initial_delay)
            if self._stopped:
                return
            while True:
                try:
                    async with self._dist_lock:
                        if self._stopped:
                            return
                        await self._event_producer.produce_event(self._event_factory())
                        if self._stopped:
                            return
                        await asyncio.sleep(self.interval)
                except asyncio.TimeoutError:  # timeout raised from etcd lock
                    log.warn("timeout raised while trying to acquire lock. retrying...")
        except asyncio.CancelledError:
            pass

    async def join(self) -> None:
        self._tick_task = asyncio.create_task(self.generate_tick())

    async def leave(self) -> None:
        self._stopped = True
        await asyncio.sleep(0)
        if not self._tick_task.done():
            try:
                self._tick_task.cancel()
                await self._tick_task
            except asyncio.CancelledError:
                pass


class LeaderGlobalTimer:

    """
    Executes the given async function only once in the given interval,
    uniquely among multiple manager instances across multiple nodes.
    """

    _event_producer: Final[EventProducer]
    _tick_task: Optional[asyncio.Task]

    def __init__(
        self,
        node_id: str,
        event_producer: EventProducer,
        event_dispatcher: EventDispatcher,
        event_factory: Callable[[], AbstractEvent],
        interval: float = 10.0,
        initial_delay: float = 0.0,
        # TODO: Initial leadership(?)
    ) -> None:
        self._id = str(uuid.uuid4())
        self._event_producer = event_producer
        self._event_dispatcher = event_dispatcher
        self._event_factory = event_factory
        self._stopped = False
        self.interval = interval
        self.initial_delay = initial_delay
        self._tick_task = None

        self._event_handlers = (
            event_dispatcher.subscribe(
                GlobalTimerJoinEvent, None, self._on_global_timer_join_event
            ),
            event_dispatcher.subscribe(
                GlobalTimerLeaveEvent, None, self._on_global_timer_leave_event
            ),
        )

        loop = asyncio.get_running_loop()
        loop.create_task(
            event_producer.produce_event(
                GlobalTimerCreatedEvent(node_id=node_id, timer_id=self._id)
            )
        )

    def __del__(self):
        for handler in self._event_handlers:
            self._event_dispatcher.unsubscribe(handler)

    async def generate_tick(self) -> None:
        try:
            await asyncio.sleep(self.initial_delay)
            if self._stopped:
                return
            while True:
                log.warning(
                    f"[GlobalTimer:{os.getpid()}:{self._id[:4]}] generate_tick(interval={self.interval})"
                )
                try:
                    if self._stopped:
                        return
                    await self._event_producer.produce_event(self._event_factory())
                    if self._stopped:
                        return
                    await asyncio.sleep(self.interval)
                except asyncio.TimeoutError:  # timeout raised from etcd lock
                    log.warn("timeout raised while trying to acquire lock. retrying...")
        except asyncio.CancelledError:
            pass

    async def join(self) -> None:
        self._stopped = False
        if self._tick_task is None:
            self._tick_task = asyncio.create_task(self.generate_tick())

    async def leave(self) -> None:
        self._stopped = True
        await asyncio.sleep(0)
        if (task := self._tick_task) is None:
            return
        self._tick_task = None
        if not task.done():
            try:
                task.cancel()
                await task
            except asyncio.CancelledError:
                pass

    async def _on_global_timer_join_event(
        self, context: None, source: str, event: GlobalTimerJoinEvent
    ):
        if event.timer_id == self._id:
            await self.join()

    async def _on_global_timer_leave_event(
        self, context: None, source: str, event: GlobalTimerLeaveEvent
    ):
        if event.timer_id == self._id:
            await self.leave()


"""
class GlobalTimerManager:

    global_timers: Final[List[GlobalTimer]] = []

    @staticmethod
    def create_timer(
        event_producer: EventProducer,
        event_factory: Callable[[], AbstractEvent],
        interval: float = 10.0,
        initial_delay: float = 0.0,
    ) -> GlobalTimer:
        global_timer = GlobalTimer(
            event_producer=event_producer,
            event_factory=event_factory,
            interval=interval,
            initial_delay=initial_delay,
        )
        GlobalTimerManager.global_timers.append(global_timer)
        return global_timer
"""
