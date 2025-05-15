from __future__ import annotations

import asyncio
import logging
import time
import uuid
import weakref
from dataclasses import dataclass
from typing import (
    Awaitable,
    Callable,
    Concatenate,
    Final,
    Mapping,
    Optional,
    Protocol,
    TypeAlias,
    Union,
)

from redis.asyncio import Redis
from redis.asyncio.client import Pipeline

from ai.backend.common.bgtask.types import BgtaskStatus
from ai.backend.common.exception import BackendAIError, BgtaskNotFoundError, ErrorCode
from ai.backend.logging import BraceStyleAdapter

from .. import redis_helper
from ..events.bgtask import (
    BaseBgtaskEvent,
    BgtaskAlreadyDoneEvent,
    BgtaskCancelledEvent,
    BgtaskDoneEvent,
    BgtaskFailedEvent,
    BgtaskPartialSuccessEvent,
    BgtaskUpdatedEvent,
)
from ..events.dispatcher import (
    EventProducer,
)
from ..types import DispatchResult, RedisConnectionInfo, Sentinel

sentinel: Final = Sentinel.TOKEN
log = BraceStyleAdapter(logging.getLogger(__spec__.name))


BgtaskEvents: TypeAlias = (
    BgtaskUpdatedEvent
    | BgtaskDoneEvent
    | BgtaskCancelledEvent
    | BgtaskFailedEvent
    | BgtaskPartialSuccessEvent
)

_MAX_BGTASK_ARCHIVE_PERIOD: Final = 86400  # 24  hours


@dataclass
class _BgTaskInfo:
    status: BgtaskStatus
    msg: str
    started_at: str
    last_update: str
    current: str = "0"
    total: str = "0"

    @classmethod
    def started(cls, msg: str = "") -> _BgTaskInfo:
        now = str(time.time())
        return cls(
            status=BgtaskStatus.STARTED,
            msg=msg,
            started_at=now,
            last_update=now,
            current="0",
            total="0",
        )

    @classmethod
    def finished(cls, status: BgtaskStatus, msg: str = "") -> _BgTaskInfo:
        now = str(time.time())
        return cls(
            status=status,
            msg=msg,
            started_at="0",
            last_update=now,
            current="0",
            total="0",
        )

    def to_dict(self) -> Mapping[str | bytes, str]:
        return {
            "status": str(self.status),
            "msg": self.msg,
            "started_at": self.started_at,
            "last_update": self.last_update,
            "current": self.current,
            "total": self.total,
        }


class ProgressReporter:
    total_progress: Union[int, float]
    current_progress: Union[int, float]

    _event_producer: Final[EventProducer]
    _redis_client: RedisConnectionInfo
    _task_id: Final[uuid.UUID]

    def __init__(
        self,
        redis_client: RedisConnectionInfo,
        event_producer: EventProducer,
        task_id: uuid.UUID,
        current_progress: int = 0,
        total_progress: int = 0,
    ) -> None:
        self._redis_client = redis_client
        self._event_producer = event_producer
        self._task_id = task_id
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

        async def _pipe_builder(r: Redis) -> Pipeline:
            pipe = r.pipeline(transaction=False)
            tracker_key = f"bgtask.{self._task_id}"
            await pipe.hset(
                tracker_key,
                mapping={
                    "current": str(current),
                    "total": str(total),
                    "msg": message or "",
                    "last_update": str(time.time()),
                },
            )
            await pipe.expire(tracker_key, _MAX_BGTASK_ARCHIVE_PERIOD)
            return pipe

        await redis_helper.execute(self._redis_client, _pipe_builder)
        await self._event_producer.produce_event(
            BgtaskUpdatedEvent(
                self._task_id,
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
    def observe_bgtask_done(
        self, *, task_name: str, status: str, duration: float, error_code: Optional[ErrorCode]
    ) -> None: ...


class NopBackgroundTaskObserver:
    def observe_bgtask_started(self, *, task_name: str) -> None:
        pass

    def observe_bgtask_done(
        self, *, task_name: str, status: str, duration: float, error_code: Optional[ErrorCode]
    ) -> None:
        pass


class BackgroundTaskManager:
    _redis_client: RedisConnectionInfo
    _event_producer: EventProducer
    _ongoing_tasks: weakref.WeakSet[asyncio.Task]
    _metric_observer: BackgroundTaskObserver
    _dict_lock: asyncio.Lock

    def __init__(
        self,
        redis_client: RedisConnectionInfo,
        event_producer: EventProducer,
        *,
        bgtask_observer: BackgroundTaskObserver = NopBackgroundTaskObserver(),
    ) -> None:
        self._redis_client = redis_client
        self._event_producer = event_producer
        self._ongoing_tasks = weakref.WeakSet()
        self._metric_observer = bgtask_observer
        self._dict_lock = asyncio.Lock()

    async def fetch_last_finished_event(
        self,
        task_id: uuid.UUID,
    ) -> Optional[BaseBgtaskEvent]:
        tracker_key = _tracker_id(task_id)
        task_info_dict = await redis_helper.execute(
            self._redis_client,
            lambda r: r.hgetall(tracker_key),
            encoding="utf-8",
        )
        if task_info_dict is None:
            # The task ID is invalid or represents a task completed more than timeout.
            raise BgtaskNotFoundError("No such background task.")

        task_info_dict["status"] = BgtaskStatus(task_info_dict["status"])
        task_info = _BgTaskInfo(**task_info_dict)
        if not task_info.status.finished():
            return None

        return BgtaskAlreadyDoneEvent(
            task_id=task_id,
            message=task_info.msg,
            task_status=task_info.status,
            current=task_info.current,
            total=task_info.total,
        )

    async def start(
        self,
        func: BackgroundTask,
        name: Optional[str] = None,
        **kwargs,
    ) -> uuid.UUID:
        task_id = uuid.uuid4()
        await self._update_bgtask_status(task_id=task_id, status=BgtaskStatus.STARTED, msg="")
        task = asyncio.create_task(self._wrapper_task(func, task_id, name, **kwargs))
        self._ongoing_tasks.add(task)
        return task_id

    async def shutdown(self) -> None:
        log.info("Cancelling remaining background tasks...")
        for task in self._ongoing_tasks.copy():
            if task.done():
                continue
            try:
                task.cancel()
                await task
            except asyncio.CancelledError:
                pass

    async def _update_bgtask_status(
        self,
        task_id: uuid.UUID,
        status: BgtaskStatus,
        msg: str = "",
    ) -> None:
        tracker_key = _tracker_id(task_id)

        async def _pipe_builder(r: Redis) -> Pipeline:
            pipe = r.pipeline()
            task_info: _BgTaskInfo
            if status.finished():
                task_info = _BgTaskInfo.finished(status=status, msg=msg)
            else:
                task_info = _BgTaskInfo.started(msg=msg)
            mapping = task_info.to_dict()
            pipe.hset(tracker_key, mapping=mapping)
            pipe.expire(tracker_key, _MAX_BGTASK_ARCHIVE_PERIOD)
            return pipe

        await redis_helper.execute(self._redis_client, _pipe_builder)

    def _convert_bgtask_to_event(
        self, task_id: uuid.UUID, bgtask_result: DispatchResult | str | None
    ) -> BaseBgtaskEvent:
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
    ) -> BaseBgtaskEvent:
        reporter = ProgressReporter(self._redis_client, self._event_producer, task_id)
        bgtask_result = await func(reporter, **kwargs)
        return self._convert_bgtask_to_event(task_id, bgtask_result)

    async def _observe_bgtask(
        self,
        func: BackgroundTask,
        task_id: uuid.UUID,
        task_name: Optional[str],
        **kwargs,
    ) -> BaseBgtaskEvent:
        self._metric_observer.observe_bgtask_started(task_name=task_name or func.__name__)
        start_time = time.perf_counter()

        try:
            bgtask_result_event = await self._run_bgtask(func, task_id, **kwargs)
        except asyncio.CancelledError:
            return BgtaskCancelledEvent(task_id, "")
        except BackendAIError as e:
            duration = time.perf_counter() - start_time
            self._metric_observer.observe_bgtask_done(
                task_name=task_name or func.__name__,
                status="bgtask_failed",
                duration=duration,
                error_code=e.error_code(),
            )
            log.exception("Task %s (%s): BackendAIError: %s", task_id, task_name, e)
            return BgtaskFailedEvent(task_id, repr(e))
        except Exception as e:
            duration = time.perf_counter() - start_time
            self._metric_observer.observe_bgtask_done(
                task_name=task_name or func.__name__,
                status="bgtask_failed",
                duration=duration,
                error_code=ErrorCode.default(),
            )
            log.exception("Task %s (%s): unhandled error", task_id, task_name)
            return BgtaskFailedEvent(task_id, repr(e))

        duration = time.perf_counter() - start_time
        self._metric_observer.observe_bgtask_done(
            task_name=task_name or func.__name__,
            status=bgtask_result_event.event_name(),
            duration=duration,
            error_code=None,
        )

        msg = getattr(bgtask_result_event, "msg", "") or ""
        task_status = bgtask_result_event.status()
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
        await self._event_producer.produce_event(bgtask_result_event)
        log.info(
            "Task {} ({}): {}", task_id, task_name or "", bgtask_result_event.__class__.__name__
        )


def _tracker_id(task_id: uuid.UUID) -> str:
    return f"bgtask.{task_id}"
