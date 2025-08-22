from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import (
    Awaitable,
    Callable,
    Concatenate,
    Final,
    Optional,
    Protocol,
    Self,
    TypeAlias,
)

from ai.backend.common.bgtask.types import (
    BackgroundTaskMetadata,
    BgtaskStatus,
    TaskID,
    TaskName,
)
from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.events.types import EventCacheDomain
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.logging import BraceStyleAdapter

from ..events.dispatcher import (
    EventProducer,
)
from ..events.event_types.bgtask.broadcast import (
    BaseBgtaskDoneEvent,
    BgtaskCancelledEvent,
    BgtaskDoneEvent,
    BgtaskFailedEvent,
    BgtaskPartialSuccessEvent,
    BgtaskUpdatedEvent,
)
from ..types import DispatchResult, Sentinel
from .reporter import ProgressReporter
from .task.base import BaseBackgroundTask

sentinel: Final = Sentinel.TOKEN
log = BraceStyleAdapter(logging.getLogger(__spec__.name))


BgtaskEvents: TypeAlias = (
    BgtaskUpdatedEvent
    | BgtaskDoneEvent
    | BgtaskCancelledEvent
    | BgtaskFailedEvent
    | BgtaskPartialSuccessEvent
)


_HEARTBEAT_INTERVAL = 60  # 1 minute
_HEARTBEAT_CHECK_INTERVAL = 300  # 5 minutes


@dataclass
class BgTaskInfo:
    status: BgtaskStatus
    msg: str
    started_at: str
    last_update: str
    current: str = "0"
    total: str = "0"

    @classmethod
    def started(cls, msg: str = "") -> Self:
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
    def finished(cls, status: BgtaskStatus, msg: str = "") -> Self:
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
    _event_producer: EventProducer
    _ongoing_tasks: dict[TaskID, asyncio.Task]
    _metric_observer: BackgroundTaskObserver
    _dict_lock: asyncio.Lock

    _valkey_client: ValkeyBgtaskClient
    _server_id: str
    _tags: set[str]
    _task_registry: Mapping[TaskName, type[BaseBackgroundTask]]

    def __init__(
        self,
        event_producer: EventProducer,
        *,
        valkey_client: ValkeyBgtaskClient,
        server_id: str,
        task_registry: Optional[Mapping[TaskName, type[BaseBackgroundTask]]] = None,
        tags: Optional[Iterable[str]] = None,
        bgtask_observer: BackgroundTaskObserver = NopBackgroundTaskObserver(),
    ) -> None:
        self._event_producer = event_producer
        self._ongoing_tasks = {}
        self._metric_observer = bgtask_observer
        self._dict_lock = asyncio.Lock()

        self._valkey_client = valkey_client
        self._server_id = server_id
        self._tags = set(tags) if tags is not None else set()
        self._task_registry = task_registry or {}

        self._heartbeat_loop_task = asyncio.create_task(self._heartbeat_loop())
        self._retry_loop_task = asyncio.create_task(self._retry_loop())

    async def start(
        self,
        func: BackgroundTask,
        name: Optional[str] = None,
        **kwargs,
    ) -> uuid.UUID:
        task_id = uuid.uuid4()
        await self._event_producer.broadcast_event_with_cache(
            EventCacheDomain.BGTASK.cache_id(task_id),
            BgtaskUpdatedEvent(
                task_id=task_id,
                message="Task started",
                current_progress=0,
                total_progress=0,
            ),
        )
        asyncio.create_task(self._wrapper_task(func, TaskID(task_id), name, **kwargs))
        return task_id

    async def shutdown(self) -> None:
        log.info("Cancelling remaining background tasks...")
        for task in self._ongoing_tasks.values():
            if task.done():
                continue
            try:
                task.cancel()
                await task
            except asyncio.CancelledError:
                pass
        try:
            self._heartbeat_loop_task.cancel()
            await self._heartbeat_loop_task
        except asyncio.CancelledError:
            pass
        try:
            self._retry_loop_task.cancel()
            await self._retry_loop_task
        except asyncio.CancelledError:
            pass

    def _convert_bgtask_to_event(
        self, task_id: uuid.UUID, bgtask_result: DispatchResult | str | None
    ) -> BaseBgtaskDoneEvent:
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
    ) -> BaseBgtaskDoneEvent:
        reporter = ProgressReporter(self._event_producer, task_id)
        bgtask_result = await func(reporter, **kwargs)
        return self._convert_bgtask_to_event(task_id, bgtask_result)

    async def _observe_bgtask(
        self,
        func: BackgroundTask,
        task_id: uuid.UUID,
        task_name: Optional[str],
        **kwargs,
    ) -> BaseBgtaskDoneEvent:
        self._metric_observer.observe_bgtask_started(task_name=task_name or func.__name__)
        start_time = time.perf_counter()
        task_name = task_name or func.__name__
        status = BgtaskStatus.STARTED
        error_code: Optional[ErrorCode] = None
        msg = "no message"
        try:
            bgtask_result_event = await self._run_bgtask(func, task_id, **kwargs)
            status = bgtask_result_event.status()
            msg = bgtask_result_event.message or msg
        except asyncio.CancelledError:
            status = BgtaskStatus.CANCELLED
            error_code = ErrorCode(
                domain=ErrorDomain.BGTASK,
                operation=ErrorOperation.EXECUTE,
                error_detail=ErrorDetail.CANCELED,
            )
            log.warning("Task {} ({}): cancelled", task_id, task_name)
            msg = "Task cancelled"
            return BgtaskCancelledEvent(task_id, msg)
        except BackendAIError as e:
            status = BgtaskStatus.FAILED
            error_code = e.error_code()
            log.exception("Task {} ({}): BackendAIError: {}", task_id, task_name, e)
            msg = repr(e)
            return BgtaskFailedEvent(task_id, msg)
        except Exception as e:
            status = BgtaskStatus.FAILED
            error_code = ErrorCode(
                domain=ErrorDomain.BGTASK,
                operation=ErrorOperation.EXECUTE,
                error_detail=ErrorDetail.INTERNAL_ERROR,
            )
            log.exception("Task {} ({}): unhandled error: {}", task_id, task_name, e)
            msg = repr(e)
            return BgtaskFailedEvent(task_id, msg)
        finally:
            duration = time.perf_counter() - start_time
            self._metric_observer.observe_bgtask_done(
                task_name=task_name,
                status=status,
                duration=duration,
                error_code=error_code,
            )

        return bgtask_result_event

    async def _process_bgtask(
        self,
        func: BackgroundTask,
        metadata: BackgroundTaskMetadata,
        **kwargs,
    ) -> None:
        bgtask_result_event = await self._observe_bgtask(
            func, metadata.task_id, metadata.task_name, **kwargs
        )
        cache_id = EventCacheDomain.BGTASK.cache_id(metadata.task_id)
        await self._event_producer.broadcast_event_with_cache(cache_id, bgtask_result_event)
        log.info(
            "Task {} ({}): {}",
            metadata.task_id,
            metadata.task_name or "",
            bgtask_result_event.__class__.__name__,
        )

    async def _wrapper_task(
        self,
        func: BackgroundTask,
        task_id: TaskID,
        task_name: Optional[str],
        **kwargs,
    ) -> None:
        current_task = asyncio.current_task()
        if current_task is not None:
            self._ongoing_tasks[task_id] = current_task
        task_metadata = BackgroundTaskMetadata.create(
            task_id=task_id,
            task_name=task_name or func.__name__,
            body=kwargs,
            server_id=self._server_id,
        )
        await self._valkey_client.register_task(task_metadata)
        try:
            await self._process_bgtask(func, task_metadata, **kwargs)
        finally:
            self._ongoing_tasks.pop(task_id, None)
            await self._valkey_client.unregister_task(task_metadata)

    async def _heartbeat_loop(self) -> None:
        """Periodically update heartbeat for running background tasks"""
        while True:
            try:
                # Update heartbeat for all ongoing background tasks
                alive_task_ids: list[TaskID] = []
                for task_id, bg_task in self._ongoing_tasks.items():
                    if not bg_task.done():
                        alive_task_ids.append(task_id)
                await self._valkey_client.heartbeat(alive_task_ids)
            except Exception as e:
                log.exception("Exception in heartbeat loop: {}", e)
            await asyncio.sleep(_HEARTBEAT_INTERVAL)

    async def _retry_loop(self) -> None:
        """Main recovery loop that checks for failed/stale tasks"""
        while True:
            try:
                await self._check_server_tasks()
                await self._check_tagged_tasks()
            except Exception as e:
                log.exception("Exception in retry loop: {}", e)
            await asyncio.sleep(_HEARTBEAT_CHECK_INTERVAL)

    async def _check_server_tasks(self) -> None:
        timeout_task_metadata = await self._valkey_client.list_timeout_tasks_by_server_id(
            self._server_id
        )

        for metadata in timeout_task_metadata:
            await self._retry_bgtask(metadata)

    async def _check_tagged_tasks(self) -> None:
        """Check tasks for a specific server type"""
        timeout_task_metadata = await self._valkey_client.list_timeout_tasks_by_tags(self._tags)

        for metadata in timeout_task_metadata:
            await self._retry_bgtask(metadata)

    async def _retry_bgtask(self, metadata: BackgroundTaskMetadata) -> None:
        """Retry a background task"""

        metadata.server_id = self._server_id  # Claim the task
        try:
            task_func = self._task_registry[TaskName(metadata.task_name)]
        except KeyError:
            log.warning(
                "Task {} ({}) is not registered in the task registry. Cannot retry.",
                metadata.task_id,
                metadata.task_name,
            )
            return
        args = task_func.get_args_from_metadata(metadata.body)
        retried_task = self._wrapper_task(task_func.execute, metadata.task_id, **args.to_dict())
        asyncio.create_task(retried_task)
