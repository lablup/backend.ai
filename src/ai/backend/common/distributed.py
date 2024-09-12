from __future__ import annotations

import abc
import asyncio
import logging
from typing import TYPE_CHECKING, Callable, Final

from aiomonitor.task import preserve_termination_log
from raftify import RaftNode

from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from .events import AbstractEvent, EventProducer
    from .lock import AbstractDistributedLock


log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AbstractGlobalTimer(metaclass=abc.ABCMeta):
    _event_producer: Final[EventProducer]
    _event_factory: Final[Callable[[], AbstractEvent]]
    _stopped: bool
    interval: float
    initial_delay: float
    task_name: str | None

    def __init__(
        self,
        event_producer: EventProducer,
        event_factory: Callable[[], AbstractEvent],
        interval: float = 10.0,
        initial_delay: float = 0.0,
        *,
        task_name: str | None = None,
    ) -> None:
        self._event_producer = event_producer
        self._event_factory = event_factory
        self._stopped = False
        self.interval = interval
        self.initial_delay = initial_delay
        self.task_name = task_name

    async def join(self) -> None:
        self._tick_task = asyncio.create_task(self.generate_tick())
        if self.task_name is not None:
            self._tick_task.set_name(self.task_name)

    async def leave(self) -> None:
        self._stopped = True
        await asyncio.sleep(0)
        if not self._tick_task.done():
            try:
                self._tick_task.cancel()
                await self._tick_task
            except asyncio.CancelledError:
                pass

    @abc.abstractmethod
    async def generate_tick(self) -> None:
        raise NotImplementedError


class RaftGlobalTimer(AbstractGlobalTimer):
    """
    Executes the given async function only once in the given interval,
    uniquely among multiple manager instances across multiple nodes.
    """

    def __init__(
        self,
        raft_node: RaftNode,
        event_producer: EventProducer,
        event_factory: Callable[[], AbstractEvent],
        interval: float = 10.0,
        initial_delay: float = 0.0,
        *,
        task_name: str | None = None,
    ) -> None:
        super().__init__(
            event_producer, event_factory, interval, initial_delay, task_name=task_name
        )
        self.raft_node = raft_node

    async def generate_tick(self) -> None:
        try:
            await asyncio.sleep(self.initial_delay)
            if self._stopped:
                return
            while True:
                try:
                    if self._stopped:
                        return
                    if await self.raft_node.is_leader():
                        await self._event_producer.produce_event(self._event_factory())
                    if self._stopped:
                        return
                    await asyncio.sleep(self.interval)
                except asyncio.TimeoutError:  # timeout raised from etcd lock
                    log.warn("timeout raised while trying to acquire lock. retrying...")
        except asyncio.CancelledError:
            pass


class DistributedLockGlobalTimer(AbstractGlobalTimer):
    """
    Executes the given async function only once in the given interval,
    uniquely among multiple manager instances across multiple nodes.
    """

    def __init__(
        self,
        dist_lock: AbstractDistributedLock,
        event_producer: EventProducer,
        event_factory: Callable[[], AbstractEvent],
        interval: float = 10.0,
        initial_delay: float = 0.0,
        *,
        task_name: str | None = None,
    ) -> None:
        super().__init__(
            event_producer, event_factory, interval, initial_delay, task_name=task_name
        )
        self._dist_lock = dist_lock

    @preserve_termination_log
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
                    if self._stopped:
                        return
                    log.warning("timeout raised while trying to acquire lock. retrying...")
        except asyncio.CancelledError:
            pass
