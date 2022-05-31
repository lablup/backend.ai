from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
import weakref
from typing import (
    Awaitable,
    Callable,
    Final,
    Literal,
    Optional,
    TypeAlias,
    Union,
    Set,
    Type,
)

import aioredis
import aioredis.client
from aiohttp import web
from aiohttp_sse import sse_response

from . import redis
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
log = BraceStyleAdapter(logging.getLogger('ai.backend.manager.background'))
TaskResult = Literal['bgtask_done', 'bgtask_cancelled', 'bgtask_failed']
BgtaskEvents: TypeAlias = BgtaskUpdatedEvent | BgtaskDoneEvent | BgtaskCancelledEvent | BgtaskFailedEvent

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

    async def update(self, increment: Union[int, float] = 0, message: str = None):
        self.current_progress += increment
        # keep the state as local variables because they might be changed
        # due to interleaving at await statements below.
        current, total = self.current_progress, self.total_progress
        redis_producer = self.event_producer.redis_client

        def _pipe_builder(r: aioredis.Redis) -> aioredis.client.Pipeline:
            pipe = r.pipeline(transaction=False)
            tracker_key = f'bgtask.{self.task_id}'
            pipe.hset(tracker_key, mapping={
                'current': str(current),
                'total': str(total),
                'msg': message or '',
                'last_update': str(time.time()),
            })
            pipe.expire(tracker_key, MAX_BGTASK_ARCHIVE_PERIOD)
            return pipe

        await redis.execute(redis_producer, _pipe_builder)
        await self.event_producer.produce_event(
            BgtaskUpdatedEvent(
                self.task_id,
                message=message,
                current_progress=current,
                total_progress=total,
            ),
        )


BackgroundTask = Callable[[ProgressReporter], Awaitable[Optional[str]]]


class BackgroundTaskManager:
    event_producer: EventProducer
    ongoing_tasks: weakref.WeakSet[asyncio.Task]
    task_update_queues: Set[asyncio.Queue[Sentinel | BgtaskEvents]]

    def __init__(self, event_producer: EventProducer) -> None:
        self.event_producer = event_producer
        self.ongoing_tasks = weakref.WeakSet()
        self.task_update_queues = set()

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
        for q in self.task_update_queues:
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
        tracker_key = f'bgtask.{task_id}'
        redis_producer = self.event_producer.redis_client
        task_info = await redis.execute(
            redis_producer,
            lambda r: r.hgetall(tracker_key),
            encoding='utf-8',
        )

        log.debug('task info: {}', task_info)
        if task_info is None:
            # The task ID is invalid or represents a task completed more than 24 hours ago.
            raise ValueError('No such background task.')

        if task_info['status'] != 'started':
            # It is an already finished task!
            async with sse_response(request) as resp:
                try:
                    body = {
                        'task_id': str(task_id),
                        'status': task_info['status'],
                        'current_progress': task_info['current'],
                        'total_progress': task_info['total'],
                        'message': task_info['msg'],
                    }
                    await resp.send(json.dumps(body), event=f"task_{task_info['status']}")
                finally:
                    await resp.send('{}', event="server_close")
            return resp

        # It is an ongoing task.
        my_queue: asyncio.Queue[BgtaskEvents | Sentinel] = asyncio.Queue()
        self.task_update_queues.add(my_queue)
        try:
            async with sse_response(request) as resp:
                try:
                    while True:
                        event = await my_queue.get()
                        try:
                            if event is sentinel:
                                break
                            if task_id != event.task_id:
                                continue
                            body = {
                                'task_id': str(task_id),
                                'message': event.message,
                            }
                            if isinstance(event, BgtaskUpdatedEvent):
                                body['current_progress'] = event.current_progress
                                body['total_progress'] = event.total_progress
                            await resp.send(json.dumps(body), event=event.name, retry=5)
                            if (isinstance(event, BgtaskDoneEvent) or
                                isinstance(event, BgtaskFailedEvent) or
                                isinstance(event, BgtaskCancelledEvent)):
                                await resp.send('{}', event="server_close")
                                break
                        finally:
                            my_queue.task_done()
                finally:
                    return resp
        finally:
            self.task_update_queues.remove(my_queue)

    async def start(
        self,
        func: BackgroundTask,
        name: str = None,
    ) -> uuid.UUID:
        task_id = uuid.uuid4()
        redis_producer = self.event_producer.redis_client

        def _pipe_builder(r: aioredis.Redis) -> aioredis.client.Pipeline:
            pipe = r.pipeline()
            tracker_key = f'bgtask.{task_id}'
            now = str(time.time())
            pipe.hset(tracker_key, mapping={
                'status': 'started',
                'current': '0',
                'total': '0',
                'msg': '',
                'started_at': now,
                'last_update': now,
            })
            pipe.expire(tracker_key, MAX_BGTASK_ARCHIVE_PERIOD)
            return pipe

        await redis.execute(redis_producer, _pipe_builder)

        task = asyncio.create_task(self._wrapper_task(func, task_id, name))
        self.ongoing_tasks.add(task)
        return task_id

    async def _wrapper_task(
        self,
        func: BackgroundTask,
        task_id: uuid.UUID,
        task_name: Optional[str],
    ) -> None:
        task_result: TaskResult
        reporter = ProgressReporter(self.event_producer, task_id)
        message = ''
        event_cls: Type[BgtaskDoneEvent] | Type[BgtaskCancelledEvent] | Type[BgtaskFailedEvent] = \
            BgtaskDoneEvent
        try:
            message = await func(reporter) or ''
            task_result = 'bgtask_done'
        except asyncio.CancelledError:
            task_result = 'bgtask_cancelled'
            event_cls = BgtaskCancelledEvent
        except Exception as e:
            task_result = 'bgtask_failed'
            event_cls = BgtaskFailedEvent
            message = repr(e)
            log.exception("Task {} ({}): unhandled error", task_id, task_name)
        finally:
            redis_producer = self.event_producer.redis_client

            async def _pipe_builder(r: aioredis.Redis):
                pipe = r.pipeline()
                tracker_key = f'bgtask.{task_id}'
                pipe.hset(tracker_key, mapping={
                    'status': task_result[7:],  # strip "bgtask_"
                    'msg': message,
                    'last_update': str(time.time()),
                })
                pipe.expire(tracker_key, MAX_BGTASK_ARCHIVE_PERIOD)
                await pipe.execute()

            await redis.execute(redis_producer, _pipe_builder)
            await self.event_producer.produce_event(
                event_cls(
                    task_id,
                    message=message,
                ),
            )
            log.info('Task {} ({}): {}', task_id, task_name or '', task_result)

    async def shutdown(self) -> None:
        join_tasks = []
        log.info('Cancelling remaining background tasks...')
        for task in self.ongoing_tasks.copy():
            if task.done():
                continue
            try:
                task.cancel()
                await task
            except asyncio.CancelledError:
                pass
        for tq in self.task_update_queues:
            tq.put_nowait(sentinel)
            join_tasks.append(tq.join())
        await asyncio.gather(*join_tasks)
