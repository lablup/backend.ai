from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Optional

from ai.backend.logging import BraceStyleAdapter

from .registry import BackgroundTaskRegistry
from .types import (
    BackgroundTaskMetadata,
    BgtaskStatus,
    ServerComponentID,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class BackgroundTaskRecoveryArgs:
    """Arguments for TaskRecovery initialization"""

    registry: BackgroundTaskRegistry
    server_id: ServerComponentID
    bg_ongoing_tasks: dict[uuid.UUID, asyncio.Task]


class BackgroundTaskRecovery:
    """Handles recovery and retry of failed/stale background tasks"""

    def __init__(self, args: BackgroundTaskRecoveryArgs) -> None:
        self._registry = args.registry
        self._server_id = args.server_id
        self._bg_ongoing_tasks = args.bg_ongoing_tasks
        self._running = True
        self._bg_recovery_task = asyncio.create_task(self._recovery_loop())

    async def stop(self) -> None:
        """Stop the background recovery loop"""
        self._running = False
        if self._bg_recovery_task:
            self._bg_recovery_task.cancel()
            try:
                await self._bg_recovery_task
            except asyncio.CancelledError:
                pass
        log.info("Stopped background task recovery loop")

    async def _recovery_loop(self) -> None:
        """Main recovery loop that checks for failed/stale tasks"""
        check_interval = 60  # Check every minute

        while self._running:
            try:
                await asyncio.sleep(check_interval)

                server_tasks = await self._registry.get_server_tasks(self._server_id.server_id)
                for task_id in server_tasks:
                    metadata = await self._registry.get_task(task_id)
                    if metadata is None:
                        continue

                    # Check if task is stale and can be retried
                    if self._should_retry_task(metadata):
                        task = await self._retry_task(metadata)
                        self._bg_ongoing_tasks[task_id] = task

                server_type_tasks = await self._registry.get_server_type_tasks(
                    self._server_id.server_type
                )
                for task_id in server_type_tasks:
                    metadata = await self._registry.get_task(task_id)
                    if metadata is None:
                        continue

                    # Check if task is stale and can be retried
                    if self._should_retry_task(metadata):
                        task = await self._retry_task(metadata)
                        self._bg_ongoing_tasks[task_id] = task

            except asyncio.CancelledError:
                break
            except Exception as e:
                log.exception("Exception in recovery loop: {}", e)

    def _should_retry_task(
        self, task: BackgroundTaskMetadata, current_time: Optional[float] = None
    ) -> bool:
        """Check if a task is stale and should be retried"""
        now = current_time or time.time()
        return now - task.updated_at > task.ttl_seconds

    def _filter_tasks_to_retry(
        self, tasks: Iterable[BackgroundTaskMetadata]
    ) -> list[BackgroundTaskMetadata]:
        """Filter tasks that can be retried based on their metadata"""
        return [task for task in tasks if self._should_retry_task(task)]

    async def _retry_task(self, task: BackgroundTaskMetadata) -> asyncio.Task:
        """Retry a background task"""

        try:
            # Update task for retry
            task.update_for_retry()
            task.server_id = self._server_id.server_id  # Claim the task
            await self._registry.update_task(task)

            # TODO: Handle checkpoint-based resume for resumable tasks
            # - Check if task has checkpoint data
            # - If checkpoint exists, pass it to handler for resuming
            # - Handler should be able to continue from checkpoint

            # The handler should be a BackgroundTask function
            # It will be called through BackgroundTaskManager.start()
            # For now, we just mark it as ready for retry
            # The actual retry logic will be implemented in the application layer
            async def func() -> None:
                pass

            return asyncio.create_task(func)  # Placeholder for actual task handler

        except Exception as e:
            log.exception("Failed to retry background task {}: {}", task.task_id, e)
            task.status = BgtaskStatus.FAILED
            task.error_message = f"Retry failed: {e}"
            await self._registry.update_task(task)
