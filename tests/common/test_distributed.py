from __future__ import annotations

import asyncio
from multiprocessing import Event, Process, Queue
import tempfile
import threading
import time
from decimal import Decimal
from functools import partial
from pathlib import Path
from typing import (
    Any,
    Iterable,
    List,
)

import attr
from etcetra.types import HostPortPair as EtcdHostPortPair
import pytest

from ai.backend.common.distributed import GlobalTimer
from ai.backend.common.events import AbstractEvent, EventDispatcher, EventProducer
from ai.backend.common.lock import EtcdLock, FileLock
from ai.backend.common.types import AgentId, EtcdRedisConfig, HostPortPair

from ai.backend.common.etcd import AsyncEtcd, ConfigScopes


def drange(start: Decimal, stop: Decimal, step: Decimal) -> Iterable[Decimal]:
    while start < stop:
        yield start
        start += step


def dslice(start: Decimal, stop: Decimal, num: int):
    """
    A simplified version of numpy.linspace with default options
    """
    delta = stop - start
    step = delta / (num - 1)
    yield from (start + step * Decimal(tick) for tick in range(0, num))


@attr.s(slots=True, frozen=True)
class NoopEvent(AbstractEvent):
    name = "_noop"

    test_ns: str = attr.ib()

    def serialize(self) -> tuple:
        return (self.test_ns, )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(value[0])


class TimerNode(threading.Thread):

    def __init__(
        self,
        lock_path: Path,
        interval: float,
        thread_idx: int,
        test_ns: str,
        event_records: List[float],
    ) -> None:
        super().__init__()
        self.lock_path = lock_path
        self.interval = interval
        self.thread_idx = thread_idx
        self.test_ns = test_ns
        self.event_records = event_records

    async def timer_node_async(self) -> None:
        self.loop = asyncio.get_running_loop()
        self.stop_event = asyncio.Event()

        async def _tick(context: Any, source: AgentId, event: NoopEvent) -> None:
            print("_tick")
            self.event_records.append(time.monotonic())

        redis_config = EtcdRedisConfig(addr=HostPortPair("127.0.0.1", 9379))
        event_dispatcher = await EventDispatcher.new(
            redis_config,
            node_id=self.test_ns,
        )
        event_producer = await EventProducer.new(
            redis_config,
        )
        event_dispatcher.consume(NoopEvent, None, _tick)

        timer = GlobalTimer(
            FileLock(self.lock_path, timeout=0, debug=True),
            event_producer,
            lambda: NoopEvent(self.test_ns),
            self.interval,
        )
        try:
            await timer.join()
            await self.stop_event.wait()
        finally:
            await timer.leave()
            await event_producer.close()
            await event_dispatcher.close()

    def run(self) -> None:
        asyncio.run(self.timer_node_async())


@pytest.mark.asyncio
async def test_global_timer_filelock(request, test_ns, redis_container) -> None:
    lock_path = Path(tempfile.gettempdir()) / f'{test_ns}.lock'
    request.addfinalizer(partial(lock_path.unlink, missing_ok=True))
    event_records: List[float] = []
    num_threads = 7
    num_records = 0
    delay = 3.0
    interval = 0.5
    target_count = (delay / interval)
    threads: List[TimerNode] = []
    for thread_idx in range(num_threads):
        timer_node = TimerNode(
            lock_path,
            interval,
            thread_idx,
            test_ns,
            event_records,
        )
        threads.append(timer_node)
        timer_node.start()
    print(f"spawned {num_threads} timers")
    print(threads)
    print("waiting")
    time.sleep(delay)
    print("stopping timers")
    for timer_node in threads:
        timer_node.loop.call_soon_threadsafe(timer_node.stop_event.set)
    print("joining timer threads")
    for timer_node in threads:
        timer_node.join()
    print("checking records")
    print(event_records)
    num_records = len(event_records)
    print(f"{num_records=}")
    assert target_count - 2 <= num_records <= target_count + 2


def etcd_timer_node_process(
    queue, stop_event, etcd_addr: EtcdHostPortPair, namespace: str,
    lock_name: str, test_ns: str, interval: float,
):
    asyncio.set_event_loop(asyncio.new_event_loop())

    async def _main():

        async def _tick(context: Any, source: AgentId, event: NoopEvent) -> None:
            print("_tick")
            queue.put(time.monotonic())

        redis_config = EtcdRedisConfig(addr=HostPortPair("127.0.0.1", 9379))
        event_dispatcher = await EventDispatcher.new(
            redis_config,
            node_id=test_ns,
        )
        event_producer = await EventProducer.new(
            redis_config,
        )
        event_dispatcher.consume(NoopEvent, None, _tick)

        etcd = AsyncEtcd(addr=etcd_addr, namespace=namespace, scope_prefix_map={
            ConfigScopes.GLOBAL: 'global',
            ConfigScopes.SGROUP: 'sgroup/testing',
            ConfigScopes.NODE: 'node/i-test',
        })
        timer = GlobalTimer(
            EtcdLock(lock_name, etcd, timeout=None, debug=True),
            event_producer,
            lambda: NoopEvent(test_ns),
            interval,
        )
        try:
            await timer.join()
            while not stop_event.is_set():
                await asyncio.sleep(0)
        finally:
            await timer.leave()
            await event_producer.close()
            await event_dispatcher.close()

    asyncio.run(_main())


@pytest.mark.asyncio
async def test_global_timer_etcdlock(
    test_ns, etcd_addr, redis_container,
) -> None:
    lock_name = f'{test_ns}lock'
    event_records_queue: Queue = Queue()
    num_processes = 7
    num_records = 0
    delay = 3.0
    interval = 0.5
    target_count = (delay / interval)
    processes: List[Process] = []
    stop_event = Event()
    for proc_idx in range(num_processes):
        process = Process(
            target=etcd_timer_node_process,
            name=f'proc-{proc_idx}',
            args=(
                event_records_queue, stop_event, etcd_addr, test_ns,
                lock_name, test_ns, interval,
            ),
        )
        process.start()
        processes.append(process)
    print(f"spawned {num_processes} timers")
    print(processes)
    print("waiting")
    time.sleep(delay)
    print("stopping timers")
    stop_event.set()
    print("joining timer processes")
    for timer_node in processes:
        timer_node.join()
    print("checking records")
    event_records: List[float] = []
    while not event_records_queue.empty():
        event_records.append(event_records_queue.get())
    print(event_records)
    num_records = len(event_records)
    print(f"{num_records=}")
    assert target_count - 2 <= num_records <= target_count + 2


@pytest.mark.asyncio
async def test_global_timer_join_leave(request, test_ns, redis_container) -> None:

    event_records = []

    async def _tick(context: Any, source: AgentId, event: NoopEvent) -> None:
        print("_tick")
        event_records.append(time.monotonic())

    redis_config = EtcdRedisConfig(addr=HostPortPair("127.0.0.1", 9379))
    event_dispatcher = await EventDispatcher.new(
        redis_config,
        node_id=test_ns,
    )
    event_producer = await EventProducer.new(
        redis_config,
    )
    event_dispatcher.consume(NoopEvent, None, _tick)

    lock_path = Path(tempfile.gettempdir()) / f'{test_ns}.lock'
    request.addfinalizer(partial(lock_path.unlink, missing_ok=True))
    for _ in range(10):
        timer = GlobalTimer(
            FileLock(lock_path, timeout=0, debug=True),
            event_producer,
            lambda: NoopEvent(test_ns),
            0.01,
        )
        await timer.join()
        await timer.leave()

    await event_producer.close()
    await event_dispatcher.close()
