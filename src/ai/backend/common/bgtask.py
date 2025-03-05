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
    Concatenate,
    DefaultDict,
    Final,
    Literal,
    Mapping,
    Optional,
    Protocol,
    Set,
    TypeAlias,
    Union,
    cast,
)

from aiohttp import web
from aiohttp_sse import EventSourceResponse, sse_response
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline

from ai.backend.logging import BraceStyleAdapter

from . import redis_helper
from .events import (
    AbstractBgtaskDoneEventType,
    BgtaskCancelledEvent,
    BgtaskDoneEvent,
    BgtaskFailedEvent,
    BgtaskPartialSuccessEvent,
    BgtaskUpdatedEvent,
    EventDispatcher,
    EventProducer,
)
from .types import AgentId, DispatchResult, Sentinel

sentinel: Final = Sentinel.TOKEN
log = BraceStyleAdapter(logging.getLogger(__spec__.name))
TaskStatus = Literal[
    "bgtask_started", "bgtask_done", "bgtask_cancelled", "bgtask_failed", "bgtask_partial_success"
]
BgtaskEvents: TypeAlias = (
    BgtaskUpdatedEvent
    | BgtaskDoneEvent
    | BgtaskCancelledEvent
    | BgtaskFailedEvent
    | BgtaskPartialSuccessEvent
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


BackgroundTask = Callable[
    Concatenate[ProgressReporter, ...], Awaitable[str | DispatchResult | None]
]


class BackgroundTaskObserver(Protocol):
    def observe_bgtask_started(self, *, task_name: str) -> None: ...
    def observe_bgtask_done(self, *, task_name: str, status: str, duration: float) -> None: ...


class NopBackgroundTaskObserver:
    def observe_bgtask_started(self, *, task_name: str) -> None:
        pass

    def observe_bgtask_done(self, *, task_name: str, status: str, duration: float) -> None:
        pass


class BackgroundTaskManager:
    event_producer: EventProducer
    ongoing_tasks: weakref.WeakSet[asyncio.Task]
    task_update_queues: DefaultDict[uuid.UUID, Set[asyncio.Queue[Sentinel | BgtaskEvents]]]
    dict_lock: asyncio.Lock

    _metric_observer: BackgroundTaskObserver

    def __init__(
        self,
        event_producer: EventProducer,
        *,
        bgtask_observer: BackgroundTaskObserver = NopBackgroundTaskObserver(),
    ) -> None:
        self.event_producer = event_producer
        self.ongoing_tasks = weakref.WeakSet()
        self.task_update_queues = defaultdict(set)
        self.dict_lock = asyncio.Lock()
        self._metric_observer = bgtask_observer

    def register_event_handlers(self, event_dispatcher: EventDispatcher) -> None:
        """
        Add bgtask related event handlers to the given event dispatcher.
        """
        event_dispatcher.subscribe(BgtaskUpdatedEvent, None, self._enqueue_bgtask_status_update)
        event_dispatcher.subscribe(BgtaskDoneEvent, None, self._enqueue_bgtask_status_update)
        event_dispatcher.subscribe(
            BgtaskPartialSuccessEvent,
            None,
            self._enqueue_bgtask_status_update,
            # TODO: Remove below event name overriding after renaming BgtaskPartialSuccessEvent
            override_event_name="bgtask_partial_success",
        )
        event_dispatcher.subscribe(BgtaskCancelledEvent, None, self._enqueue_bgtask_status_update)
        event_dispatcher.subscribe(BgtaskFailedEvent, None, self._enqueue_bgtask_status_update)

    async def _enqueue_bgtask_status_update(
        self,
        context: None,
        source: AgentId,
        event: BgtaskEvents,
    ) -> None:
        task_id = event.task_id
        if task_id is None:
            raise ValueError(f"Task ID is not set in the {event.name} event!")

        for q in self.task_update_queues[task_id]:
            q.put_nowait(event)

    async def _send_event(
        self, resp: EventSourceResponse, event: BgtaskEvents, extra_data: dict
    ) -> None:
        body = event.event_body(extra_data)
        await resp.send(
            json.dumps(body),
            event=event.event_name(extra_data),
            retry=event.retry_count(),
        )
        if event.should_close():
            await resp.send("{}", event="server_close")

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
                    await self._send_event(resp, event, extra_data)

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
        name: Optional[str] = None,
        **kwargs,
    ) -> uuid.UUID:
        task_id = uuid.uuid4()
        await self._update_bgtask_status(task_id=task_id, status="bgtask_started", msg="")
        task = asyncio.create_task(self._wrapper_task(func, task_id, name, **kwargs))
        self.ongoing_tasks.add(task)
        return task_id

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

    async def _update_bgtask_status(
        self,
        task_id: uuid.UUID,
        status: TaskStatus,
        msg: str = "",
    ) -> None:
        redis_producer = self.event_producer.redis_client
        tracker_key = f"bgtask.{task_id}"

        async def _pipe_builder(r: Redis) -> Pipeline:
            pipe = r.pipeline()
            status_str = status.removeprefix("bgtask_") if status.startswith("bgtask_") else status

            now = str(time.time())
            mapping: Mapping[str | bytes, Any] = {
                "status": status_str,
                "msg": msg,
                "last_update": now,
            }

            if status == "started":
                mapping = {
                    **mapping,
                    "current": "0",
                    "total": "0",
                    "started_at": now,
                }

            pipe.hset(tracker_key, mapping=mapping)
            pipe.expire(tracker_key, MAX_BGTASK_ARCHIVE_PERIOD)
            return pipe

        await redis_helper.execute(redis_producer, _pipe_builder)

    def _convert_bgtask_to_event(
        self, task_id: uuid.UUID, bgtask_result: DispatchResult | str | None
    ) -> AbstractBgtaskDoneEventType:
        # legacy
        if bgtask_result is None or isinstance(bgtask_result, str):
            return BgtaskDoneEvent(task_id, bgtask_result)

        message = bgtask_result.message()
        if bgtask_result.has_error():
            return BgtaskPartialSuccessEvent(
                task_id=task_id, message=message, errors=bgtask_result.errors
            )
        else:
            return BgtaskDoneEvent(task_id=task_id, message=message)

    async def _run_bgtask(
        self,
        func: BackgroundTask,
        task_id: uuid.UUID,
        **kwargs,
    ) -> AbstractBgtaskDoneEventType:
        reporter = ProgressReporter(self.event_producer, task_id)
        bgtask_result = await func(reporter, **kwargs)
        return self._convert_bgtask_to_event(task_id, bgtask_result)

    async def _observe_bgtask(
        self,
        func: BackgroundTask,
        task_id: uuid.UUID,
        task_name: Optional[str],
        **kwargs,
    ) -> AbstractBgtaskDoneEventType:
        self._metric_observer.observe_bgtask_started(task_name=task_name or func.__name__)
        start_time = time.perf_counter()

        try:
            bgtask_result_event = await self._run_bgtask(func, task_id, **kwargs)
        except asyncio.CancelledError:
            return BgtaskCancelledEvent(task_id, "")

        except Exception as e:
            duration = time.perf_counter() - start_time
            self._metric_observer.observe_bgtask_done(
                task_name=task_name or func.__name__, status="bgtask_failed", duration=duration
            )
            log.exception("Task %s (%s): unhandled error", task_id, task_name)
            return BgtaskFailedEvent(task_id, repr(e))

        duration = time.perf_counter() - start_time
        self._metric_observer.observe_bgtask_done(
            task_name=task_name or func.__name__,
            status=bgtask_result_event.name,
            duration=duration,
        )

        msg = getattr(bgtask_result_event, "msg", "") or ""
        task_status = cast(TaskStatus, bgtask_result_event.name)
        await self._update_bgtask_status(task_id, task_status, msg=msg)

        return bgtask_result_event

    async def _wrapper_task(
        self,
        func: BackgroundTask,
        task_id: uuid.UUID,
        task_name: Optional[str],
        **kwargs,
    ) -> None:
        bgtask_result_event = await self._observe_bgtask(func, task_id, task_name, **kwargs)
        await self.event_producer.produce_event(bgtask_result_event)
        log.info(
            "Task {} ({}): {}", task_id, task_name or "", bgtask_result_event.__class__.__name__
        )
