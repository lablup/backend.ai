from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
import weakref
from collections import defaultdict
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    DefaultDict,
    Final,
    Literal,
    Set,
    Type,
    TypeAlias,
    Union,
)

from aiohttp import web
from aiohttp_sse import sse_response
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline

from . import redis_helper
from .events import (
    BgtaskCancelledEvent,
    BgtaskDoneEvent,
    BgtaskFailedEvent,
    BgtaskUpdatedEvent,
    EventDispatcher,
    EventProducer,
)
from .logging import BraceStyleAdapter
from .types import AgentId, Sentinel

sentinel: Final = Sentinel.TOKEN
log = BraceStyleAdapter(logging.getLogger(__spec__.name))
TaskStatus = Literal["bgtask_started", "bgtask_done", "bgtask_cancelled", "bgtask_failed"]
BgtaskEvents: TypeAlias = (
    BgtaskUpdatedEvent | BgtaskDoneEvent | BgtaskCancelledEvent | BgtaskFailedEvent
)

MAX_BGTASK_ARCHIVE_PERIOD: Final = 86400  # 24  hours


class ProgressReporter:
    event_producer: Final[EventProducer]
    task_id: Final[uuid.UUID]
    total_progress: Union[int, float]
    current_progress: Union[int, float]

    def __init__(
        self,
        event_dispatcher: EventProducer,
        task_id: uuid.UUID,
        current_progress: int = 0,
        total_progress: int = 0,
    ) -> None:
        self.event_producer = event_dispatcher
        self.task_id = task_id
        self.current_progress = current_progress
        self.total_progress = total_progress

    async def update(
        self,
        increment: Union[int, float] = 0,
        message: str | None = None,
    ) -> None:
        self.current_progress += increment
        # keep the state as local variables because they might be changed
        # due to interleaving at await statements below.
        current, total = self.current_progress, self.total_progress
        redis_producer = self.event_producer.redis_client

        async def _pipe_builder(r: Redis) -> Pipeline:
            pipe = r.pipeline(transaction=False)
            tracker_key = f"bgtask.{self.task_id}"
            await pipe.hset(
                tracker_key,
                mapping={
                    "current": str(current),
                    "total": str(total),
                    "msg": message or "",
                    "last_update": str(time.time()),
                },
            )
            await pipe.expire(tracker_key, MAX_BGTASK_ARCHIVE_PERIOD)
            return pipe

        await redis_helper.execute(redis_producer, _pipe_builder)
        await self.event_producer.produce_event(
            BgtaskUpdatedEvent(
                self.task_id,
                message=message,
                current_progress=current,
                total_progress=total,
            ),
        )


BackgroundTask = Callable[[ProgressReporter], Awaitable[str | None]]


class BackgroundTaskManager:
    event_producer: EventProducer
    ongoing_tasks: weakref.WeakSet[asyncio.Task]
    task_update_queues: DefaultDict[uuid.UUID, Set[asyncio.Queue[Sentinel | BgtaskEvents]]]
    dict_lock: asyncio.Lock

    def __init__(self, event_producer: EventProducer) -> None:
        self.event_producer = event_producer
        self.ongoing_tasks = weakref.WeakSet()
        self.task_update_queues = defaultdict(set)
        self.dict_lock = asyncio.Lock()

    def register_event_handlers(self, event_dispatcher: EventDispatcher) -> None:
        """
        Add bgtask related event handlers to the given event dispatcher.
        """
        event_dispatcher.subscribe(BgtaskUpdatedEvent, None, self._enqueue_bgtask_status_update)
        event_dispatcher.subscribe(BgtaskDoneEvent, None, self._enqueue_bgtask_status_update)
        event_dispatcher.subscribe(BgtaskCancelledEvent, None, self._enqueue_bgtask_status_update)
        event_dispatcher.subscribe(BgtaskFailedEvent, None, self._enqueue_bgtask_status_update)

    async def _enqueue_bgtask_status_update(
        self,
        context: None,
        source: AgentId,
        event: BgtaskEvents,
    ) -> None:
        task_id = event.task_id
        for q in self.task_update_queues[task_id]:
            q.put_nowait(event)

    async def push_bgtask_events(
        self,
        request: web.Request,
        task_id: uuid.UUID,
    ) -> web.StreamResponse:
        """
        A aiohttp-based server-sent events (SSE) responder that pushes the bgtask updates
        to the clients.
        """
        async with sse_response(request) as resp:
            try:
                async for event, extra_data in self.poll_bgtask_event(task_id):
                    body: dict[str, Any] = {
                        "task_id": str(event.task_id),
                        "message": event.message,
                    }
                    match event:
                        case BgtaskUpdatedEvent():
                            body["current_progress"] = event.current_progress
                            body["total_progress"] = event.total_progress
                            await resp.send(json.dumps(body), event=event.name, retry=5)
                        case BgtaskDoneEvent():
                            if extra_data:
                                body.update(extra_data)
                                await resp.send(
                                    json.dumps(body), event="bgtask_" + extra_data["status"]
                                )
                            else:
                                await resp.send("{}", event="bgtask_done")
                            await resp.send("{}", event="server_close")
                        case BgtaskCancelledEvent() | BgtaskFailedEvent():
                            await resp.send("{}", event="server_close")
            except:
                log.exception("")
                raise
            finally:
                return resp

    async def poll_bgtask_event(
        self,
        task_id: uuid.UUID,
    ) -> AsyncIterator[tuple[BgtaskEvents, dict]]:
        """
        RHS of return tuple will be filled with extra informations when needed
        (e.g. progress information of task when callee is trying to poll information of already completed one)
        """
        tracker_key = f"bgtask.{task_id}"
        redis_producer = self.event_producer.redis_client
        task_info = await redis_helper.execute(
            redis_producer,
            lambda r: r.hgetall(tracker_key),
            encoding="utf-8",
        )

        if task_info is None:
            # The task ID is invalid or represents a task completed more than 24 hours ago.
            raise ValueError("No such background task.")

        if task_info["status"] != "started":
            # It is an already finished task!
            yield (
                BgtaskDoneEvent(task_id, message=task_info["msg"]),
                {
                    "status": task_info["status"],
                    "current_progress": task_info["current"],
                    "total_progress": task_info["total"],
                },
            )
            return

        # It is an ongoing task.
        my_queue: asyncio.Queue[BgtaskEvents | Sentinel] = asyncio.Queue()
        async with self.dict_lock:
            self.task_update_queues[task_id].add(my_queue)
        try:
            while True:
                event = await my_queue.get()
                try:
                    if event is sentinel:
                        break
                    if task_id != event.task_id:
                        continue
                    yield event, {}
                finally:
                    my_queue.task_done()
        finally:
            self.task_update_queues[task_id].remove(my_queue)
            async with self.dict_lock:
                if len(self.task_update_queues[task_id]) == 0:
                    del self.task_update_queues[task_id]

    async def start(
        self,
        func: BackgroundTask,
        name: str | None = None,
        **kwargs,
    ) -> uuid.UUID:
        task_id = uuid.uuid4()
        redis_producer = self.event_producer.redis_client

        async def _pipe_builder(r: Redis) -> Pipeline:
            pipe = r.pipeline()
            tracker_key = f"bgtask.{task_id}"
            now = str(time.time())
            await pipe.hset(
                tracker_key,
                mapping={
                    "status": "started",
                    "current": "0",
                    "total": "0",
                    "msg": "",
                    "started_at": now,
                    "last_update": now,
                },
            )
            await pipe.expire(tracker_key, MAX_BGTASK_ARCHIVE_PERIOD)
            return pipe

        await redis_helper.execute(redis_producer, _pipe_builder)

        task = asyncio.create_task(self._wrapper_task(func, task_id, name, **kwargs))
        self.ongoing_tasks.add(task)
        return task_id

    async def _wrapper_task(
        self,
        func: BackgroundTask,
        task_id: uuid.UUID,
        task_name: str | None,
        **kwargs,
    ) -> None:
        task_status: TaskStatus = "bgtask_started"
        reporter = ProgressReporter(self.event_producer, task_id)
        message = ""
        event_cls: Type[BgtaskDoneEvent] | Type[BgtaskCancelledEvent] | Type[BgtaskFailedEvent] = (
            BgtaskDoneEvent
        )
        try:
            message = await func(reporter, **kwargs) or ""
            task_status = "bgtask_done"
        except asyncio.CancelledError:
            task_status = "bgtask_cancelled"
            event_cls = BgtaskCancelledEvent
        except Exception as e:
            task_status = "bgtask_failed"
            event_cls = BgtaskFailedEvent
            message = repr(e)
            log.exception("Task {} ({}): unhandled error", task_id, task_name)
        finally:
            redis_producer = self.event_producer.redis_client

            async def _pipe_builder(r: Redis):
                pipe = r.pipeline()
                tracker_key = f"bgtask.{task_id}"
                await pipe.hset(
                    tracker_key,
                    mapping={
                        "status": task_status.removeprefix("bgtask_"),
                        "msg": message,
                        "last_update": str(time.time()),
                    },
                )
                await pipe.expire(tracker_key, MAX_BGTASK_ARCHIVE_PERIOD)
                return pipe

            await redis_helper.execute(redis_producer, _pipe_builder)
            await self.event_producer.produce_event(
                event_cls(
                    task_id,
                    message=message,
                ),
            )
            log.info("Task {} ({}): {}", task_id, task_name or "", task_status)

    async def shutdown(self) -> None:
        join_tasks = []
        log.info("Cancelling remaining background tasks...")
        for task in self.ongoing_tasks.copy():
            if task.done():
                continue
            try:
                task.cancel()
                await task
            except asyncio.CancelledError:
                pass
        for qset in self.task_update_queues.values():
            for tq in qset:
                tq.put_nowait(sentinel)
                join_tasks.append(tq.join())
        await asyncio.gather(*join_tasks)
