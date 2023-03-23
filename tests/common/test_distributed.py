from __future__ import annotations

import asyncio
import tempfile
import threading
import time
from dataclasses import dataclass
from decimal import Decimal
from functools import partial
from multiprocessing import Event, Process, Queue
from pathlib import Path
from typing import Any, Callable, Iterable, List, Tuple

import aiotools
import attrs
import pytest
from etcetra.types import HostPortPair as EtcdHostPortPair
from redis.asyncio import Redis

from ai.backend.common.distributed import GlobalTimer
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.events import AbstractEvent, EventDispatcher, EventProducer
from ai.backend.common.lock import AbstractDistributedLock, EtcdLock, FileLock, RedisLock
from ai.backend.common.types import AgentId, EtcdRedisConfig, HostPortPair, RedisConnectionInfo


@dataclass
class TimerNodeContext:
    test_ns: str
    redis_addr: HostPortPair
    interval: float


@dataclass
class EtcdLockContext:
    namespace: str
    addr: EtcdHostPortPair
    lock_name: str


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


@attrs.define(slots=True, frozen=True)
class NoopEvent(AbstractEvent):
    name = "_noop"

    test_ns: str = attrs.field()

    def serialize(self) -> tuple:
        return (self.test_ns,)

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(value[0])


async def run_timer(
    lock_factory: Callable[[], AbstractDistributedLock],
    stop_event: asyncio.Event,
    event_records: List[float],
    redis_addr: HostPortPair,
    test_ns: str,
    interval: int | float,
) -> None:
    async def _tick(context: Any, source: AgentId, event: NoopEvent) -> None:
        print("_tick")
        event_records.append(time.monotonic())

    redis_config = EtcdRedisConfig(addr=redis_addr)
    event_dispatcher = await EventDispatcher.new(
        redis_config,
        node_id=test_ns,
    )
    event_producer = await EventProducer.new(
        redis_config,
    )
    event_dispatcher.consume(NoopEvent, None, _tick)

    timer = GlobalTimer(
        lock_factory(),
        event_producer,
        lambda: NoopEvent(test_ns),
        interval=interval,
    )
    try:
        await timer.join()
        await stop_event.wait()
    finally:
        await timer.leave()
        await event_producer.close()
        await event_dispatcher.close()


def etcd_timer_node_process(
    queue,
    stop_event,
    etcd_ctx: EtcdLockContext,
    timer_ctx: TimerNodeContext,
) -> None:
    asyncio.set_event_loop(asyncio.new_event_loop())

    async def _main() -> None:
        async def _tick(context: Any, source: AgentId, event: NoopEvent) -> None:
            print("_tick")
            queue.put(time.monotonic())

        redis_config = EtcdRedisConfig(addr=timer_ctx.redis_addr)
        event_dispatcher = await EventDispatcher.new(
            redis_config,
            node_id=timer_ctx.test_ns,
        )
        event_producer = await EventProducer.new(
            redis_config,
        )
        event_dispatcher.consume(NoopEvent, None, _tick)

        etcd = AsyncEtcd(
            addr=etcd_ctx.addr,
            namespace=etcd_ctx.namespace,
            scope_prefix_map={
                ConfigScopes.GLOBAL: "global",
                ConfigScopes.SGROUP: "sgroup/testing",
                ConfigScopes.NODE: "node/i-test",
            },
        )
        timer = GlobalTimer(
            EtcdLock(etcd_ctx.lock_name, etcd, timeout=None, debug=True),
            event_producer,
            lambda: NoopEvent(timer_ctx.test_ns),
            timer_ctx.interval,
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


class TimerNode(threading.Thread):
    def __init__(
        self,
        event_records: list[float],
        lock_factory: Callable[[], AbstractDistributedLock],
        thread_idx: int,
        timer_ctx: TimerNodeContext,
    ) -> None:
        super().__init__()
        self.event_records = event_records
        self.lock_factory = lock_factory
        self.thread_idx = thread_idx
        self.interval = timer_ctx.interval
        self.test_ns = timer_ctx.test_ns
        self.redis_addr = timer_ctx.redis_addr

    async def timer_node_async(self) -> None:
        self.loop = asyncio.get_running_loop()
        self.stop_event = asyncio.Event()

        async def _tick(context: Any, source: AgentId, event: NoopEvent) -> None:
            print("_tick")
            self.event_records.append(time.monotonic())

        redis_config = EtcdRedisConfig(addr=self.redis_addr)
        event_dispatcher = await EventDispatcher.new(
            redis_config,
            node_id=self.test_ns,
        )
        event_producer = await EventProducer.new(
            redis_config,
        )
        event_dispatcher.consume(NoopEvent, None, _tick)

        timer = GlobalTimer(
            self.lock_factory(),
            event_producer,
            lambda: NoopEvent(self.test_ns),
            interval=self.interval,
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
    lock_path = Path(tempfile.gettempdir()) / f"{test_ns}.lock"
    request.addfinalizer(partial(lock_path.unlink, missing_ok=True))
    lock_factory = lambda: FileLock(lock_path, timeout=0, debug=True)

    event_records: List[float] = []
    num_threads = 7
    num_records = 0
    delay = 3.0
    interval = 0.5
    target_count = delay / interval
    threads: List[TimerNode] = []
    for thread_idx in range(num_threads):
        timer_node = TimerNode(
            event_records,
            lock_factory,
            thread_idx,
            TimerNodeContext(
                test_ns=test_ns,
                redis_addr=redis_container[1],
                interval=interval,
            ),
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


@pytest.mark.asyncio
async def test_gloal_timer_redlock(test_ns, redis_container) -> None:
    redis_addr = redis_container[1]
    r = RedisConnectionInfo(
        Redis.from_url(f"redis://{redis_addr.host}:{redis_addr.port}"),
        service_name=None,
    )
    lock_factory = lambda: RedisLock(f"{test_ns}lock", r, debug=True)

    event_records: List[float] = []
    num_threads = 7
    num_records = 0
    delay = 3.0
    interval = 0.5
    target_count = delay / interval
    tasks: List[Tuple[asyncio.Task, asyncio.Event]] = []
    for thread_idx in range(num_threads):
        stop_event = asyncio.Event()
        task = asyncio.create_task(
            run_timer(
                lock_factory,
                stop_event,
                event_records,
                redis_addr,
                test_ns,
                interval,
            ),
        )
        tasks.append((task, stop_event))
    print(f"spawned {num_threads} timers")
    print(tasks)
    print("waiting")
    await asyncio.sleep(delay)
    print("stopping timers")
    for _, stop_event in tasks:
        stop_event.set()
    print("joining timer tasks")
    for timer_task, _ in tasks:
        await timer_task
    print("checking records")
    print(event_records)
    num_records = len(event_records)
    print(f"{num_records=}")
    assert target_count - 2 <= num_records <= target_count + 2


@pytest.mark.asyncio
async def test_global_timer_etcdlock(
    test_ns,
    etcd_container,
    redis_container,
) -> None:
    lock_name = f"{test_ns}lock"
    event_records_queue: Queue = Queue()
    num_processes = 7
    num_records = 0
    delay = 3.0
    interval = 0.5
    target_count = delay / interval
    processes: List[Process] = []
    stop_event = Event()
    for proc_idx in range(num_processes):
        process = Process(
            target=etcd_timer_node_process,
            name=f"proc-{proc_idx}",
            args=(
                event_records_queue,
                stop_event,
                EtcdLockContext(
                    addr=etcd_container[1],
                    namespace=test_ns,
                    lock_name=lock_name,
                ),
                TimerNodeContext(
                    test_ns=test_ns,
                    redis_addr=redis_container[1],
                    interval=interval,
                ),
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

    redis_config = EtcdRedisConfig(addr=redis_container[1])
    event_dispatcher = await EventDispatcher.new(
        redis_config,
        node_id=test_ns,
    )
    event_producer = await EventProducer.new(
        redis_config,
    )
    event_dispatcher.consume(NoopEvent, None, _tick)

    lock_path = Path(tempfile.gettempdir()) / f"{test_ns}.lock"
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


@pytest.mark.asyncio
async def test_filelock_watchdog(request, test_ns) -> None:
    """
    This test case is for verifying
    if watchdog releases the lock after the timeout(ttl)
    even though the given job is in progress yet.

    TODO: For further implementation, the `FileLock` should be able to **cancel** current job after timeout.
    """
    lock_path = Path(tempfile.gettempdir()) / f"{test_ns}.lock"
    request.addfinalizer(partial(lock_path.unlink, missing_ok=True))

    loop = asyncio.get_running_loop()
    vclock = aiotools.VirtualClock()
    with vclock.patch_loop():

        async def _main(ttl: float, delay: float = 5.0, interval: float = 0.03):
            async with FileLock(lock_path, timeout=0, lifetime=ttl, debug=True) as lock:
                t = 0.0
                while lock.is_locked and t < delay:
                    await asyncio.sleep(interval)
                    t += interval

        ttl, delay = (3.0, float("inf"))
        n = 4

        begin = loop.time()

        coroutines = [asyncio.create_task(_main(ttl=ttl, delay=delay)) for _ in range(n)]
        await asyncio.gather(*coroutines)

        assert ttl * n <= (loop.time() - begin) < delay * n
