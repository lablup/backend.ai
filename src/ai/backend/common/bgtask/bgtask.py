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
)

from ai.backend.common.bgtask.task.executor import (
    BaseBackgroundTaskExecutor,
    BaseBackgroundTaskLegacyExecutor,
)
from ai.backend.common.bgtask.types import (
    BackgroundTaskDetailMetadata,
    BgtaskStatus,
    TaskDetailIdentifier,
    TaskID,
    TaskName,
)
from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.exception import (
    BgtaskNotRegisteredError,
    ErrorCode,
)
from ai.backend.logging import BraceStyleAdapter

from ..events.dispatcher import (
    EventProducer,
)
from ..types import DispatchResult, Sentinel
from .reporter import ProgressReporter
from .task.base import BaseBackgroundTaskArgs
from .task.registry import BackgroundTaskHandlerRegistry, BackgroundTaskHandlerRegistryArgs

sentinel: Final = Sentinel.TOKEN
log = BraceStyleAdapter(logging.getLogger(__spec__.name))


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
    _metric_observer: BackgroundTaskObserver
    _dict_lock: asyncio.Lock

    _valkey_client: ValkeyBgtaskClient
    _server_id: str
    _tags: set[str]
    _task_registry: BackgroundTaskHandlerRegistry

    _legacy_executor: BaseBackgroundTaskLegacyExecutor
    _executor: BaseBackgroundTaskExecutor

    _legacy_ongoing_tasks: dict[TaskID, asyncio.Task]
    _ongoing_tasks: dict[str, asyncio.Task]  # key: TaskDetailIdentifier.to_storage_key()

    def __init__(
        self,
        event_producer: EventProducer,
        *,
        task_registry: Optional[BackgroundTaskHandlerRegistry] = None,
        valkey_client: ValkeyBgtaskClient,
        server_id: str,
        tags: Optional[Iterable[str]] = None,
        bgtask_observer: Optional[BackgroundTaskObserver] = None,
    ) -> None:
        self._event_producer = event_producer
        self._metric_observer = bgtask_observer or NopBackgroundTaskObserver()
        self._dict_lock = asyncio.Lock()

        self._valkey_client = valkey_client
        self._server_id = server_id
        self._tags = set(tags) if tags is not None else set()
        self._task_registry = task_registry or BackgroundTaskHandlerRegistry(
            BackgroundTaskHandlerRegistryArgs(
                valkey_client=valkey_client,
                event_producer=event_producer,
                metric_observer=self._metric_observer,
                server_id=server_id,
            )
        )
        self._legacy_executor = BaseBackgroundTaskLegacyExecutor(
            valkey_client=valkey_client,
            event_producer=event_producer,
            metric_observer=self._metric_observer,
        )
        self._executor = BaseBackgroundTaskExecutor(
            valkey_client=valkey_client,
            event_producer=event_producer,
            metric_observer=self._metric_observer,
            server_id=server_id,
        )

        self._heartbeat_loop_task = asyncio.create_task(self._heartbeat_loop())
        self._retry_loop_task = asyncio.create_task(self._retry_loop())

    async def start(
        self,
        func: BackgroundTask,
        name: Optional[str] = None,
        **kwargs,
    ) -> uuid.UUID:
        return await self._legacy_executor.start(func, name, **kwargs)

    async def shutdown(self) -> None:
        log.info("Cancelling remaining background tasks...")

        # Shutdown all executors (both retriable and non-retriable tasks)
        await self._task_registry.shutdown_all_executors()

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

    async def start_retriable(
        self,
        task_key: str,
        task_name: TaskName,
        args: BaseBackgroundTaskArgs,
        tags: Optional[Iterable[str]] = None,
    ) -> TaskID:
        executor = self._task_registry.get_task_executor(task_name)
        return await executor.start_retriable_task(
            task_key=task_key,
            task_name=task_name,
            args=args,
            server_id=self._server_id,
            tags=tags,
        )

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

    async def _retry_bgtask(self, metadata: BackgroundTaskDetailMetadata) -> None:
        """Retry a background task"""

        metadata.server_id = self._server_id  # Claim the task
        task_name = metadata.task_name
        try:
            executor = self._task_registry.get_task_executor(task_name)
        except BgtaskNotRegisteredError:
            log.exception(
                "Task {} ({}): not registered in {} server, skipping retry",
                metadata.task_id,
                task_name,
                self._server_id,
            )
            return

        # args = executor.get_args_type().from_metadata_body(metadata.body)
        # Executor will manage the task lifecycle internally
        await executor._process_retriable_task(
            
            
        )

    async def _heartbeat_loop(self) -> None:
        """Periodically update heartbeat for running background tasks"""
        while True:
            try:
                # Update heartbeat for all ongoing background tasks
                alive_task_ids: list[TaskID | TaskDetailIdentifier] = []
                for task_id, bg_task in self._legacy_ongoing_tasks.items():
                    if not bg_task.done():
                        alive_task_ids.append(task_id)

                for task_storage_key, bg_task in self._ongoing_tasks.items():
                    if not bg_task.done():
                        alive_task_ids.append(
                            TaskDetailIdentifier.from_storage_key(task_storage_key)
                        )

                await self._valkey_client.heartbeat(
                    alive_task_ids,
                    server_id=self._server_id,
                    tags=self._tags,
                )
            except Exception as e:
                log.exception("Exception in heartbeat loop: {}", e)
            await asyncio.sleep(_HEARTBEAT_INTERVAL)
