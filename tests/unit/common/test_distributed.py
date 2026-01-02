from __future__ import annotations

import asyncio
import random
import tempfile
import threading
import time
from dataclasses import dataclass
from decimal import Decimal
from functools import partial
from pathlib import Path
from typing import Any, Callable, Iterable, List, Literal, Optional, Tuple

import aiotools
import pytest
from redis.asyncio import Redis

from ai.backend.common import config
from ai.backend.common.defs import REDIS_STREAM_DB
from ai.backend.common.distributed import GlobalTimer
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.events.dispatcher import (
    EventDispatcher,
    EventProducer,
)
from ai.backend.common.events.types import (
    AbstractAnycastEvent,
    EventDomain,
)
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.lock import (
    AbstractDistributedLock,
    EtcdLock,
    FileLock,
    RedisLock,
)
from ai.backend.common.message_queue.redis_queue import RedisMQArgs, RedisQueue
from ai.backend.common.types import AgentId, HostPortPair, RedisConnectionInfo, RedisTarget


@dataclass
class TimerNodeContext:
    test_case_ns: str
    interval: float
    redis_container: HostPortPair
    stream_key: str
    group_name: str
    node_id: str


@dataclass
class EtcdLockContext:
    namespace: str
    addrs: list[HostPortPair]
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


@dataclass
class NoopAnycastEvent(AbstractAnycastEvent):
    test_case_ns: str

    def serialize(self) -> tuple:
        return (self.test_case_ns,)

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(value[0])

    @classmethod
    def event_domain(cls) -> EventDomain:
        return EventDomain.AGENT

    def domain_id(self) -> Optional[str]:
        return None

    def user_event(self) -> Optional[UserEvent]:
        return None

    @classmethod
    def event_name(cls) -> str:
        return "noop"


EVENT_DISPATCHER_CONSUMER_GROUP = "test"


async def run_timer(
    lock_factory: Callable[[], AbstractDistributedLock],
    stop_event: asyncio.Event,
    event_records: List[float],
    redis_addr: HostPortPair,
    test_case_ns: str,
    interval: int | float,
) -> None:
    redis_target = RedisTarget(
        addr=redis_addr, redis_helper_config=config.redis_helper_default_config
    )
    node_id = f"{test_case_ns}-node-{threading.get_ident()}"
    redis_mq = await RedisQueue.create(
        redis_target,
        RedisMQArgs(
            anycast_stream_key="events",
            broadcast_channel="events_broadcast",
            consume_stream_keys={
                "events",
            },
            subscribe_channels={
                "events_broadcast",
            },
            group_name=EVENT_DISPATCHER_CONSUMER_GROUP,
            node_id=node_id,
            db=REDIS_STREAM_DB,
        ),
    )
    event_dispatcher = EventDispatcher(
        redis_mq,
    )

    async def _tick(context: Any, source: AgentId, event: NoopAnycastEvent) -> None:
        print("_tick")
        event_records.append(time.monotonic())

    event_dispatcher.consume(NoopAnycastEvent, None, _tick)
    await event_dispatcher.start()
    event_producer = EventProducer(
        redis_mq,
        source=AgentId(node_id),
    )

    timer = GlobalTimer(
        lock_factory(),
        event_producer,
        lambda: NoopAnycastEvent(test_case_ns),
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
    etcd_client: Literal["etcd-client-py"],
) -> None:
    asyncio.set_event_loop(asyncio.new_event_loop())

    async def _main() -> None:
        async def _tick(context: Any, source: AgentId, event: NoopAnycastEvent) -> None:
            print("_tick")
            queue.put(time.monotonic())

        redis_target = RedisTarget(
            addr=timer_ctx.redis_container,
            redis_helper_config={
                "socket_timeout": 5.0,
                "socket_connect_timeout": 2.0,
                "reconnect_poll_timeout": 0.3,
            },
        )
        redis_mq = await RedisQueue.create(
            redis_target,
            RedisMQArgs(
                anycast_stream_key=timer_ctx.stream_key,
                broadcast_channel="events_broadcast",
                consume_stream_keys={
                    timer_ctx.stream_key,
                },
                subscribe_channels=None,
                group_name=timer_ctx.group_name,
                node_id=timer_ctx.node_id,
                db=REDIS_STREAM_DB,
            ),
        )

        event_dispatcher = EventDispatcher(
            redis_mq,
        )
        event_producer = EventProducer(
            redis_mq,
            source=AgentId(timer_ctx.node_id),
        )
        event_dispatcher.consume(NoopAnycastEvent, None, _tick)
        await event_dispatcher.start()
        await asyncio.sleep(0.1)  # Allow dispatcher to start

        etcd_lock: AbstractDistributedLock
        match etcd_client:
            case "etcd-client-py":
                etcd = AsyncEtcd(
                    addrs=etcd_ctx.addrs,
                    namespace=etcd_ctx.namespace,
                    scope_prefix_map={
                        ConfigScopes.GLOBAL: "global",
                        ConfigScopes.SGROUP: "sgroup/testing",
                        ConfigScopes.NODE: "node/i-test",
                    },
                )
                etcd_lock = EtcdLock(etcd_ctx.lock_name, etcd, timeout=None, debug=True)

        timer = GlobalTimer(
            etcd_lock,
            event_producer,
            lambda: NoopAnycastEvent(timer_ctx.test_case_ns),
            timer_ctx.interval,
        )
        try:
            await timer.join()
            while not stop_event.is_set():
                await asyncio.sleep(0)
        finally:
            await timer.leave()
            await event_dispatcher.close()
            await event_producer.close()
            await redis_mq.close()
            await asyncio.sleep(0.2)  # Allow cleanup to complete

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
        self.test_case_ns = timer_ctx.test_case_ns
        self.redis_container = timer_ctx.redis_container
        self.stream_key = timer_ctx.stream_key
        self.group_name = timer_ctx.group_name
        self.node_id = timer_ctx.node_id

    async def timer_node_async(self) -> None:
        self.loop = asyncio.get_running_loop()
        self.stop_event = asyncio.Event()
        redis_target = RedisTarget(
            addr=self.redis_container,
            redis_helper_config={
                "socket_timeout": 5.0,
                "socket_connect_timeout": 2.0,
                "reconnect_poll_timeout": 0.3,
            },
        )
        redis_mq = await RedisQueue.create(
            redis_target,
            RedisMQArgs(
                anycast_stream_key=self.stream_key,
                broadcast_channel="events_broadcast",
                consume_stream_keys={
                    self.stream_key,
                },
                subscribe_channels={
                    "events_broadcast",
                },
                group_name=self.group_name,
                node_id=self.node_id,
                db=REDIS_STREAM_DB,
            ),
        )

        async def _tick(context: Any, source: AgentId, event: NoopAnycastEvent) -> None:
            print("_tick")
            self.event_records.append(time.monotonic())

        event_dispatcher = EventDispatcher(
            redis_mq,
        )
        event_producer = EventProducer(
            redis_mq,
            source=AgentId(self.node_id),
        )
        event_dispatcher.consume(NoopAnycastEvent, None, _tick)
        await event_dispatcher.start()

        timer = GlobalTimer(
            self.lock_factory(),
            event_producer,
            lambda: NoopAnycastEvent(self.test_case_ns),
            interval=self.interval,
        )
        try:
            await timer.join()
            await self.stop_event.wait()
        finally:
            await timer.leave()
            await event_dispatcher.close()
            await event_producer.close()

    def run(self) -> None:
        asyncio.run(self.timer_node_async())


@pytest.mark.asyncio
async def test_global_timer_filelock(
    request,
    test_case_ns,
    redis_container,
    test_node_id,
) -> None:
    lock_path = Path(tempfile.gettempdir()) / f"{test_case_ns}.lock"
    request.addfinalizer(partial(lock_path.unlink, missing_ok=True))
    lock_factory = lambda: FileLock(lock_path, timeout=0, debug=True)

    event_records: List[float] = []
    num_threads = 7
    num_records = 0
    delay = 3.0
    interval = 0.5
    target_count = delay / interval
    threads: List[TimerNode] = []
    stream_key = f"{test_case_ns}-stream-{random.randint(0, 1000)}"
    group_name = f"test-group-{random.randint(0, 1000)}"
    for thread_idx in range(num_threads):
        timer_node = TimerNode(
            event_records,
            lock_factory,
            thread_idx,
            TimerNodeContext(
                test_case_ns=test_case_ns,
                interval=interval,
                redis_container=redis_container[1],
                stream_key=stream_key,
                group_name=group_name,
                node_id=test_node_id,
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
async def test_global_timer_redlock(
    test_case_ns,
    redis_container,
) -> None:
    redis_addr = redis_container[1]
    r = RedisConnectionInfo(
        Redis.from_url(f"redis://{redis_addr.host}:{redis_addr.port}"),
        sentinel=None,
        name="test",
        service_name=None,
        redis_helper_config=config.redis_helper_default_config,
    )
    lock_factory = lambda: RedisLock(f"{test_case_ns}lock", r, debug=True)

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
                test_case_ns,
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


# Tests using Process are failing due to a compatibility issue with valkey-glide.
# @pytest.mark.asyncio
# @pytest.mark.parametrize("etcd_client", ["etcd-client-py"])
# async def test_global_timer_etcdlock(
#     test_case_ns,
#     etcd_container,
#     etcd_client,
#     redis_container,
#     test_node_id,
# ) -> None:
#     lock_name = f"{test_case_ns}lock"
#     event_records_queue: Queue = Queue()
#     num_processes = 7
#     num_records = 0
#     delay = 3.0
#     interval = 0.5
#     target_count = delay / interval
#     processes: List[Process] = []
#     stop_event = Event()
#     stream_key = f"test-stream-{random.randint(0, 1000)}"
#     group_name = f"test-group-{random.randint(0, 1000)}"
#     for proc_idx in range(num_processes):
#         process = Process(
#             target=etcd_timer_node_process,
#             name=f"proc-{proc_idx}",
#             args=(
#                 event_records_queue,
#                 stop_event,
#                 EtcdLockContext(
#                     addr=etcd_container[1],
#                     namespace=test_case_ns,
#                     lock_name=lock_name,
#                 ),
#                 TimerNodeContext(
#                     test_case_ns=test_case_ns,
#                     interval=interval,
#                     redis_container=redis_container[1],
#                     stream_key=stream_key,
#                     group_name=group_name,
#                     node_id=test_node_id,
#                 ),
#                 etcd_client,
#             ),
#         )
#         process.start()
#         processes.append(process)
#     print(f"spawned {num_processes} timers")
#     print(processes)
#     print("waiting")
#     time.sleep(delay)
#     print("stopping timers")
#     stop_event.set()
#     print("joining timer processes")
#     for timer_node in processes:
#         timer_node.join()
#     print("checking records")
#     event_records: List[float] = []
#     while not event_records_queue.empty():
#         event_records.append(event_records_queue.get())
#     print(event_records)
#     num_records = len(event_records)
#     print(f"{num_records=}")
#     assert target_count - 2 <= num_records <= target_count + 2


@pytest.mark.asyncio
async def test_global_timer_join_leave(
    request,
    test_case_ns,
    test_valkey_stream_mq,
    test_node_id,
) -> None:
    event_records = []

    async def _tick(context: Any, source: AgentId, event: NoopAnycastEvent) -> None:
        print("_tick")
        event_records.append(time.monotonic())

    event_dispatcher = EventDispatcher(
        test_valkey_stream_mq,
    )
    event_producer = EventProducer(
        test_valkey_stream_mq,
        source=AgentId(test_node_id),
    )
    event_dispatcher.consume(NoopAnycastEvent, None, _tick)
    await event_dispatcher.start()

    lock_path = Path(tempfile.gettempdir()) / f"{test_case_ns}.lock"
    request.addfinalizer(partial(lock_path.unlink, missing_ok=True))
    for _ in range(10):
        timer = GlobalTimer(
            FileLock(lock_path, timeout=0, debug=True),
            event_producer,
            lambda: NoopAnycastEvent(test_case_ns),
            0.01,
        )
        await timer.join()
        await timer.leave()

    await event_producer.close()
    await event_dispatcher.close()


@pytest.mark.asyncio
async def test_filelock_watchdog(request, test_case_ns) -> None:
    """
    This test case is for verifying
    if watchdog releases the lock after the timeout(ttl)
    even though the given job is in progress yet.

    TODO: For further implementation, the `FileLock` should be able to **cancel** current job after timeout.
    """
    lock_path = Path(tempfile.gettempdir()) / f"{test_case_ns}.lock"
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
