from __future__ import annotations

import asyncio
import functools
import logging
import time
import uuid
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, MutableMapping
from contextlib import suppress
from dataclasses import dataclass
from typing import (
    Awaitable,
    Callable,
    Concatenate,
    Final,
    Optional,
    ParamSpec,
    Self,
    Sequence,
    TypeAlias,
)

from ai.backend.common.bgtask.exception import InvalidTaskMetadataError
from ai.backend.common.bgtask.types import (
    WHOLE_TASK_KEY,
    BgTaskKey,
    BgtaskStatus,
    TaskID,
    TaskInfo,
    TaskName,
    TaskStatus,
    TaskSubKeyInfo,
    TaskTotalInfo,
    TaskType,
)
from ai.backend.common.clients.valkey_client.valkey_bgtask.client import (
    TaskSetKey,
    ValkeyBgtaskClient,
)
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
from .hooks import (
    BackgroundTaskObserver,
    CompositeTaskHook,
    EventProducerHook,
    MetricObserverHook,
    NopBackgroundTaskObserver,
    TaskContext,
    ValkeyUnregisterHook,
)
from .reporter import ProgressReporter
from .task.base import BaseBackgroundTaskArgs, BaseBackgroundTaskResult
from .task.registry import BackgroundTaskHandlerRegistry
from .task_result import TaskCancelledResult, TaskFailedResult, TaskResult, TaskSuccessResult

sentinel: Final = Sentinel.TOKEN
log = BraceStyleAdapter(logging.getLogger(__spec__.name))

P = ParamSpec("P")


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


class BackgroundTaskMeta(ABC):
    @abstractmethod
    def total_info(self) -> TaskTotalInfo:
        raise NotImplementedError

    @abstractmethod
    def retriable(self) -> bool:
        # TODO: Remove the retriable property once all migrations are complete
        raise NotImplementedError

    @abstractmethod
    def async_tasks(self) -> Sequence[asyncio.Task]:
        raise NotImplementedError

    def cancel(self) -> None:
        """Cancel all tasks."""
        for task in self.async_tasks():
            task.cancel()

    def done(self) -> bool:
        """Check if all tasks are done."""
        return all(task.done() for task in self.async_tasks())

    def cancelled(self) -> bool:
        """Check if any task was cancelled."""
        return any(task.cancelled() for task in self.async_tasks())


class LocalBgtask(BackgroundTaskMeta):
    _task: asyncio.Task

    def __init__(self, task: asyncio.Task) -> None:
        self._task = task

    def total_info(self) -> TaskTotalInfo:
        raise NotImplementedError("LocalBgtask is not recoverable and cannot be stored")

    def retriable(self) -> bool:
        return False

    def async_tasks(self) -> Sequence[asyncio.Task]:
        return [self._task]


class SingleBgtask(BackgroundTaskMeta):
    _total_info: TaskTotalInfo
    _task: asyncio.Task

    def __init__(
        self,
        total_info: TaskTotalInfo,
        task: asyncio.Task,
    ) -> None:
        self._total_info = total_info
        self._task = task

    def total_info(self) -> TaskTotalInfo:
        return self._total_info

    def retriable(self) -> bool:
        return True

    def async_tasks(self) -> Sequence[asyncio.Task]:
        return [self._task]


class ParallelBgtask(BackgroundTaskMeta):
    _total_info: TaskTotalInfo
    _tasks: Sequence[asyncio.Task]

    def __init__(
        self,
        total_info: TaskTotalInfo,
        tasks: Sequence[asyncio.Task],
    ) -> None:
        self._total_info = total_info
        self._tasks = tasks

    def total_info(self) -> TaskTotalInfo:
        return self._total_info

    def retriable(self) -> bool:
        return True

    def async_tasks(self) -> Sequence[asyncio.Task]:
        return self._tasks


def _exception_to_task_result(
    func: Callable[P, Awaitable[BaseBackgroundTaskResult]],
) -> Callable[P, Awaitable[TaskResult]]:
    """
    Decorator that converts exceptions raised during background task execution
    into TaskResult objects.

    This decorator handles:
    - asyncio.CancelledError -> TaskCancelledResult
    - BackendAIError -> TaskFailedResult with the exception
    - General Exception -> TaskFailedResult with the exception

    The decorator also handles logging of exceptions appropriately.
    """

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> TaskResult:
        try:
            result = await func(*args, **kwargs)
            return TaskSuccessResult(result)
        except asyncio.CancelledError:
            log.warning("Task cancelled")
            return TaskCancelledResult()
        except BackendAIError as e:
            log.exception("BackendAIError in task: {}", e)
            return TaskFailedResult(e)
        except Exception as e:
            log.exception("Unhandled error in task: {}", e)
            return TaskFailedResult(e)

    return wrapper


class BackgroundTaskManager:
    _event_producer: EventProducer
    _ongoing_tasks: MutableMapping[TaskID, BackgroundTaskMeta]
    _hook: CompositeTaskHook
    _metric_observer: BackgroundTaskObserver  # Keep for backward compatibility
    _valkey_client: ValkeyBgtaskClient
    _task_set_key: TaskSetKey
    _task_registry: BackgroundTaskHandlerRegistry

    _heartbeat_loop_task: asyncio.Task
    _retry_loop_task: asyncio.Task

    def __init__(
        self,
        event_producer: EventProducer,
        *,
        valkey_client: ValkeyBgtaskClient,
        server_id: str,
        tags: Optional[Iterable[str]] = None,
        bgtask_observer: BackgroundTaskObserver = NopBackgroundTaskObserver(),
        task_registry: Optional[BackgroundTaskHandlerRegistry] = None,
    ) -> None:
        self._event_producer = event_producer
        self._ongoing_tasks = {}

        self._valkey_client = valkey_client
        self._task_set_key = TaskSetKey(
            server_id=server_id, tags=set(tags) if tags is not None else set()
        )
        self._metric_observer = bgtask_observer
        self._hook = CompositeTaskHook([
            MetricObserverHook(bgtask_observer),
            EventProducerHook(event_producer),
            ValkeyUnregisterHook(valkey_client, self._task_set_key),
        ])
        self._task_registry = task_registry or BackgroundTaskHandlerRegistry()
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
            EventCacheDomain.BGTASK.cache_id(str(task_id)),
            BgtaskUpdatedEvent(
                task_id=task_id,
                message="Task started",
                current_progress=0,
                total_progress=0,
            ),
        )
        task = asyncio.create_task(self._wrapper_task(func, task_id, name, **kwargs))
        self._ongoing_tasks[TaskID(task_id)] = LocalBgtask(task=task)
        return task_id

    async def shutdown(self) -> None:
        log.info("Cancelling remaining background tasks...")
        for task in self._ongoing_tasks.values():
            async_tasks = task.async_tasks()
            for async_task in async_tasks:
                if async_task.done():
                    continue
                try:
                    async_task.cancel()
                    await async_task
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

    async def _wrapper_task(
        self,
        func: BackgroundTask,
        task_id: uuid.UUID,
        task_name: Optional[str],
        **kwargs,
    ) -> None:
        try:
            bgtask_result_event = await self._observe_bgtask(func, task_id, task_name, **kwargs)
            cache_id = EventCacheDomain.BGTASK.cache_id(str(task_id))
            await self._event_producer.broadcast_event_with_cache(cache_id, bgtask_result_event)
            log.info(
                "Task {} ({}): {}", task_id, task_name or "", bgtask_result_event.__class__.__name__
            )
        finally:
            self._ongoing_tasks.pop(TaskID(task_id), None)

    async def start_retriable(
        self,
        task_name: TaskName,
        args: BaseBackgroundTaskArgs,
    ) -> TaskID:
        task_id = TaskID(uuid.uuid4())
        task = asyncio.create_task(self._execute_new_task(task_name, task_id, WHOLE_TASK_KEY, args))

        # Create TaskTotalInfo for storage
        task_info = TaskInfo(
            task_id=task_id,
            task_name=task_name,
            task_type=TaskType.SINGLE,
            body=args.to_redis_json(),
            ongoing_count=1,
            success_count=0,
            failure_count=0,
        )
        # For single tasks, create a subtask entry representing the whole task
        whole_task_subkey = TaskSubKeyInfo(
            task_id=task_id,
            key=WHOLE_TASK_KEY,
            status=TaskStatus.ONGOING,
            last_message="",
        )
        total_info = TaskTotalInfo(task_info=task_info, task_key_list=[whole_task_subkey])

        self._ongoing_tasks[task_id] = SingleBgtask(
            total_info=total_info,
            task=task,
        )
        await self._valkey_client.register_task(total_info, self._task_set_key)
        return task_id

    @_exception_to_task_result
    async def _try_to_execute_new_task(
        self,
        task_name: TaskName,
        args: BaseBackgroundTaskArgs,
    ) -> BaseBackgroundTaskResult:
        return await self._task_registry.execute_new_task(task_name, args)

    @_exception_to_task_result
    async def _try_to_revive_task(
        self, task_name: TaskName, task_info: TaskInfo
    ) -> BaseBackgroundTaskResult:
        return await self._task_registry.revive_task(task_name, task_info.body)

    async def _execute_new_task(
        self,
        task_name: TaskName,
        task_id: TaskID,
        subkey: BgTaskKey,
        args: BaseBackgroundTaskArgs,
    ) -> None:
        async with self._hook.apply(
            TaskContext(
                task_name=task_name,
                task_id=task_id,
            )
        ) as context:
            task_status: TaskStatus = TaskStatus.SUCCESS
            last_message = "Task completed successfully"
            try:
                task_result = await self._try_to_execute_new_task(task_name, args)
                context.result = task_result
            except Exception as e:
                task_status = TaskStatus.FAILURE
                last_message = f"Task failed with exception: {e}"
                raise e
            finally:
                with suppress(Exception):
                    await self._valkey_client.finish_subtask(
                        task_id=task_id,
                        subkey=subkey,
                        status=task_status,
                        last_message=last_message,
                    )

    async def _revive_task(
        self, task_name: TaskName, task_info: TaskInfo, task_key: BgTaskKey
    ) -> None:
        async with self._hook.apply(
            TaskContext(
                task_name=task_name,
                task_id=task_info.task_id,
            )
        ) as context:
            task_status: TaskStatus = TaskStatus.SUCCESS
            last_message = "Task completed successfully"
            try:
                task_result = await self._try_to_revive_task(task_name, task_info)
                context.result = task_result
            except Exception as e:
                task_status = TaskStatus.FAILURE
                last_message = f"Task failed with exception: {e}"
                raise e
            finally:
                with suppress(Exception):
                    await self._valkey_client.finish_subtask(
                        task_id=task_info.task_id,
                        subkey=task_key,
                        status=task_status,
                        last_message=last_message,
                    )

    async def _heartbeat_loop(self) -> None:
        """Periodically update heartbeat for running background tasks"""
        while True:
            try:
                # Update heartbeat for all ongoing background tasks
                alive_task_info: list[TaskTotalInfo] = []
                for bg_task in self._ongoing_tasks.values():
                    if bg_task.retriable():
                        alive_task_info.append(bg_task.total_info())
                await self._valkey_client.heartbeat(
                    alive_task_info,
                    self._task_set_key,
                )
            except Exception as e:
                log.exception("Exception in heartbeat loop: {}", e)
            await asyncio.sleep(_HEARTBEAT_INTERVAL)

    async def _retry_loop(self) -> None:
        """Main recovery loop that checks for failed/stale tasks"""
        while True:
            try:
                unmanaged_task_total_info_list = await self._valkey_client.fetch_unmanaged_tasks(
                    self._task_set_key
                )
                async_tasks = [
                    self._retry_bgtask(total_info) for total_info in unmanaged_task_total_info_list
                ]
                results = await asyncio.gather(*async_tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, BaseException):
                        log.exception("Exception in retry loop: {}", result)
            except Exception as e:
                log.exception("Exception in retry loop: {}", e)
            await asyncio.sleep(_HEARTBEAT_CHECK_INTERVAL)

    async def _retry_bgtask(self, total_info: TaskTotalInfo) -> None:
        """Retry a background task"""

        task_info = total_info.task_info
        task_name = task_info.task_name
        async_tasks: list[asyncio.Task] = []
        for subkey_info in total_info.task_key_list:
            if subkey_info.status == TaskStatus.ONGOING:
                task_key = subkey_info.key
                async_task = asyncio.create_task(self._revive_task(task_name, task_info, task_key))
                async_tasks.append(async_task)
        task: Optional[BackgroundTaskMeta] = None
        match task_info.task_type:
            case TaskType.SINGLE:
                if len(async_tasks) != 1:
                    log.error(
                        "Inconsistent task type and subtask count for SINGLE task: {}",
                        task_info.task_id,
                    )
                    raise InvalidTaskMetadataError(
                        f"SINGLE task must have exactly one ongoing subtask: {task_info.task_id}"
                    )
                task = SingleBgtask(
                    total_info=total_info,
                    task=async_tasks[0],
                )
            case TaskType.PARALLEL:
                if len(async_tasks) < 1:
                    log.error(
                        "Inconsistent task type and subtask count for PARALLEL task: {}",
                        task_info.task_id,
                    )
                    raise InvalidTaskMetadataError(
                        f"PARALLEL task must have at least one ongoing subtask: {task_info.task_id}"
                    )
                task = ParallelBgtask(
                    tasks=async_tasks,
                    total_info=total_info,
                )
            case _:
                log.error("Unsuuported task type: {}", task_info.task_type)
                raise InvalidTaskMetadataError(f"Unsupported task type: {task_info.task_type}")
        if task is not None:
            self._ongoing_tasks[task_info.task_id] = task
        await self._valkey_client.claim_task(task_info.task_id, self._task_set_key)
