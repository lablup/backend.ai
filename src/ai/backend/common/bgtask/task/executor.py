from __future__ import annotations

import asyncio
import logging
import time
import uuid
from abc import ABC
from collections.abc import Iterable
from typing import Optional

from ai.backend.common.bgtask.bgtask import (
    BackgroundTask,
    BackgroundTaskObserver,
)
from ai.backend.common.bgtask.reporter import ProgressReporter
from ai.backend.common.bgtask.task.base import BaseBackgroundTaskArgs, BaseBackgroundTaskHandler, BaseBatchBackgroundTaskHandler
from ai.backend.common.bgtask.types import (
    BackgroundTaskDetailMetadata,
    BgtaskStatus,
    TaskDetailIdentifier,
    TaskID,
    TaskName,
)
from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.bgtask.broadcast import (
    BaseBgtaskDoneEvent,
    BgtaskCancelledEvent,
    BgtaskDoneEvent,
    BgtaskFailedEvent,
    BgtaskPartialSuccessEvent,
    BgtaskUpdatedEvent,
)
from ai.backend.common.events.types import EventCacheDomain
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.common.types import DispatchResult
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class BaseBackgroundTaskLegacyExecutor(ABC):
    _valkey_client: ValkeyBgtaskClient
    _event_producer: EventProducer
    _metric_observer: BackgroundTaskObserver

    def __init__(
        self,
        valkey_client: ValkeyBgtaskClient,
        event_producer: EventProducer,
        metric_observer: BackgroundTaskObserver,
    ) -> None:
        self._valkey_client = valkey_client
        self._event_producer = event_producer
        self._metric_observer = metric_observer

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
        # self._ongoing_tasks[TaskID(task_id)] = task
        return task_id

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
        # try:
        bgtask_result_event = await self._observe_bgtask(func, task_id, task_name, **kwargs)
        cache_id = EventCacheDomain.BGTASK.cache_id(str(task_id))
        await self._event_producer.broadcast_event_with_cache(cache_id, bgtask_result_event)
        log.info(
            "Task {} ({}): {}", task_id, task_name or "", bgtask_result_event.__class__.__name__
        )
        # finally:
        # self._ongoing_tasks.pop(TaskID(task_id), None)


class BackgroundExecutionContext:
    task_key: str
    handler: BaseBackgroundTaskHandler

    def __init__(self, task_key: str, handler: BaseBackgroundTaskHandler) -> None:
        self.task_key = task_key
        self.handler = handler


class BackgroundExecutionArgs:
    task_name: TaskName
    task_key: str
    args: BaseBackgroundTaskArgs
    
    def __init__(self, task_name: TaskName, task_key: str, args: BaseBackgroundTaskArgs) -> None:
        self.task_name = task_name
        self.task_key = task_key
        self.args = args


class BaseBackgroundTaskExecutor(ABC):
    _handler: BaseBackgroundTaskHandler
    _valkey_client: ValkeyBgtaskClient
    # _ongoing_tasks: dict[str, asyncio.Task]  # key: TaskDetailIdentifier.to_storage_key()
    _event_producer: EventProducer
    _metric_observer: BackgroundTaskObserver
    _server_id: str

    def __init__(
        self,
        handler: BaseBackgroundTaskHandler,
        valkey_client: ValkeyBgtaskClient,
        event_producer: EventProducer,
        metric_observer: BackgroundTaskObserver,
        server_id: str,
    ) -> None:
        self._handler = handler
        self._valkey_client = valkey_client
        self._event_producer = event_producer
        self._metric_observer = metric_observer
        self._server_id = server_id

    async def start_retriable(
        self,
        # TODO: 리스트로 만들기? -> 아냐 차라리 이걸 여러번 실행하자.
        # task_name: TaskName,
        # task_key: str,
        # args: BaseBackgroundTaskArgs,
        args_dict: dict[TaskName, BackgroundExecutionArgs],
        tags: Optional[Iterable[str]] = None,
    ) -> list[TaskDetailIdentifier]:
        task_id = TaskID(uuid.uuid4())
        await self._event_producer.broadcast_event_with_cache(
            EventCacheDomain.BGTASK.cache_id(str(task_id)),
            BgtaskUpdatedEvent(
                task_id=task_id,
                message="Task started",
                current_progress=0,
                total_progress=0,
            ),
        )

        result = []
        for handler_name, handler in self._handlers.items():
            args = args_dict.get(handler_name)

            if args is None:
                log.warning("No args provided for handler {}, skipping", handler_name)
                continue

            task_key = args.task_key
            task_name = args.task_name
            args = args.args

            metadata = BackgroundTaskDetailMetadata.create(
                task_key=task_key,
                task_id=task_id,
                task_name=task_name,
                body=args.to_metadata_body(),
                server_id=self._server_id,
                tags=tags,
            )
            task = asyncio.create_task(
                self._process_retriable_task(handler, args, metadata)
            )
            tid = TaskDetailIdentifier(task_id=task_id, task_key=task_key)
            # self._ongoing_tasks[tid.to_storage_key()] = task
            result.append(tid)

        return result

    async def _run_retriable_bgtask(
        self,
        func: BaseBackgroundTaskHandler,
        args: BaseBackgroundTaskArgs,
    ) -> DispatchResult:
        return await func.execute(args)

    def _convert_result_to_event(
        self,
        bgtask_result: DispatchResult,
        metadata: BackgroundTaskDetailMetadata,
    ) -> BaseBgtaskDoneEvent:
        task_id = metadata.task_id
        message = bgtask_result.message()
        if bgtask_result.has_error():
            return BgtaskPartialSuccessEvent(
                task_id=task_id, message=message, errors=bgtask_result.errors
            )
        else:
            return BgtaskDoneEvent(task_id=task_id, message=message)

    async def _observe_retriable_bgtask(
        self,
        func: BaseBackgroundTaskHandler,
        args: BaseBackgroundTaskArgs,
        metadata: BackgroundTaskDetailMetadata,
    ) -> BaseBgtaskDoneEvent:
        task_name = func.name()
        task_id = metadata.task_id
        self._metric_observer.observe_bgtask_started(task_name=task_name)
        start_time = time.perf_counter()
        status = BgtaskStatus.STARTED
        error_code: Optional[ErrorCode] = None
        msg = "no message"
        try:
            result = await self._run_retriable_bgtask(func, args)
            bgtask_result_event = self._convert_result_to_event(result, metadata)
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

    async def _wrapper_broadcast_result(
        self,
        func: BaseBackgroundTaskHandler,
        args: BaseBackgroundTaskArgs,
        metadata: BackgroundTaskDetailMetadata,
    ) -> None:
        bgtask_result_event = await self._observe_retriable_bgtask(
            func,
            args,
            metadata,
        )
        cache_id = EventCacheDomain.BGTASK.cache_id(str(metadata.task_id))
        await self._event_producer.broadcast_event_with_cache(cache_id, bgtask_result_event)
        log.info(
            "Task {} ({}): {}",
            metadata.task_id,
            metadata.task_name or "",
            bgtask_result_event.__class__.__name__,
        )

    async def _process_retriable_task(
        self,
        func: BaseBackgroundTaskHandler,
        args: BaseBackgroundTaskArgs,
        metadata: BackgroundTaskDetailMetadata,
    ) -> None:
        await self._valkey_client.register_task(metadata)
        try:
            await self._wrapper_broadcast_result(
                func,
                args,
                metadata,
            )
        finally:
            key = metadata.task_detail_identifier.to_storage_key()
            # self._ongoing_tasks.pop(key, None)
            await self._valkey_client.unregister_task(metadata)

    # def get_handlers(self) -> list[BaseBackgroundTaskHandler]:
    #     return self._handlers