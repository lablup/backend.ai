from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from typing import (
    Awaitable,
    Callable,
    Concatenate,
    Final,
    Mapping,
    Optional,
    Protocol,
    Self,
    TypeAlias,
    Union,
)

from ai.backend.common.clients.valkey_client.valkey_bgtask import ValkeyBgtaskClient
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
from .defs import (
    DEFAULT_HEARTBEAT_INTERVAL,
)
from .recovery import BackgroundTaskRecovery, BackgroundTaskRecoveryArgs
from .registry import BackgroundTaskRegistry, BackgroundTaskRegistryArgs
from .types import (
    BackgroundTaskMetadata,
    BackgroundTaskRetryArgs,
    BgtaskStatus,
    ServerComponentID,
)

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


class ProgressReporter:
    total_progress: Union[int, float]
    current_progress: Union[int, float]

    _event_producer: Final[EventProducer]
    _task_id: Final[uuid.UUID]

    def __init__(
        self,
        event_producer: EventProducer,
        task_id: uuid.UUID,
        current_progress: int = 0,
        total_progress: int = 0,
    ) -> None:
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
        await self._event_producer.broadcast_event_with_cache(
            EventCacheDomain.BGTASK.cache_id(self._task_id),
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


@dataclass
class BackgroundTaskManagerArgs:
    """Arguments for BackgroundTaskManager initialization"""

    server_id: ServerComponentID
    event_producer: EventProducer
    valkey_client: ValkeyBgtaskClient
    bgtask_observer: BackgroundTaskObserver = NopBackgroundTaskObserver()


class BackgroundTaskManager:
    _event_producer: EventProducer
    _bgtask_ongoing_tasks: dict[uuid.UUID, asyncio.Task]
    _metric_observer: BackgroundTaskObserver
    _dict_lock: asyncio.Lock
    _server_id: ServerComponentID
    _bgtask_registry: BackgroundTaskRegistry
    _bgtask_recovery: BackgroundTaskRecovery

    _bgtask_heartbeat_task: asyncio.Task
    _bgtask_handlers: dict[str, BackgroundTask]

    def __init__(
        self,
        args: BackgroundTaskManagerArgs,
    ) -> None:
        self._event_producer = args.event_producer
        self._bgtask_ongoing_tasks = {}
        self._metric_observer = args.bgtask_observer
        self._dict_lock = asyncio.Lock()

        # Initialize from args if provided
        self._server_id = args.server_id

        self._bgtask_registry = BackgroundTaskRegistry(
            BackgroundTaskRegistryArgs(valkey_client=args.valkey_client)
        )
        self._bgtask_recovery = BackgroundTaskRecovery(
            BackgroundTaskRecoveryArgs(
                registry=self._bgtask_registry,
                server_id=args.server_id,
                bg_ongoing_tasks=self._bgtask_ongoing_tasks,
            )
        )
        self._bgtask_heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        self._bgtask_handlers = {}

    async def start(
        self,
        func: BackgroundTask,
        name: Optional[str] = None,
        *,
        retry_args: Optional[BackgroundTaskRetryArgs] = None,
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
        task = asyncio.create_task(self._wrapper_task(func, task_id, name, retry_args, **kwargs))
        self._bgtask_ongoing_tasks[task_id] = task
        return task_id

    async def shutdown(self) -> None:
        log.info("Cancelling remaining background tasks...")

        # Stop recovery
        await self._bgtask_recovery.stop()

        # Cancel heartbeat task
        self._bgtask_heartbeat_task.cancel()
        try:
            await self._bgtask_heartbeat_task
        except asyncio.CancelledError:
            pass

        # Cancel all ongoing tasks
        for task in self._bgtask_ongoing_tasks.values():
            if task.done():
                continue
            try:
                task.cancel()
                await task
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

    async def _wrapper_task(
        self,
        func: BackgroundTask,
        task_id: uuid.UUID,
        task_name: Optional[str],
        retry_args: Optional[BackgroundTaskRetryArgs],
        **kwargs,
    ) -> None:
        # Register task in registry
        if retry_args is not None:
            bgtask_metadata = BackgroundTaskMetadata.create(
                task_id=task_id,
                task_name=task_name or func.__name__,
                body=retry_args.body,
                server_id=self._server_id,
                allow_any_server=retry_args.allow_any_server,
                max_retries=retry_args.max_retries,
            )
            await self._bgtask_registry.save_task(bgtask_metadata)
        bgtask_result_event = await self._observe_bgtask(func, task_id, task_name, **kwargs)
        cache_id = EventCacheDomain.BGTASK.cache_id(task_id)
        await self._event_producer.broadcast_event_with_cache(cache_id, bgtask_result_event)
        await self._bgtask_registry.delete_task(task_id)
        log.info(
            "Task {} ({}): {}", task_id, task_name or "", bgtask_result_event.__class__.__name__
        )

    async def _heartbeat_loop(self) -> None:
        """Periodically update heartbeat for running background tasks"""
        while True:
            try:
                await asyncio.sleep(DEFAULT_HEARTBEAT_INTERVAL)

                # Update heartbeat for all ongoing background tasks
                for task_id, bg_task in self._bgtask_ongoing_tasks.items():
                    if not bg_task.done():
                        await self._bgtask_registry.update_heartbeat(task_id)
            except Exception as e:
                log.exception("Error in heartbeat loop: {}", e)
