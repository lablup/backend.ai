from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Optional

from ai.backend.logging import BraceStyleAdapter

from .defs import DEFAULT_TASK_RETRY_TTL
from .registry import BackgroundTaskRegistry
from .types import (
    BackgroundTaskMetadata,
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

                await self._check_server_tasks()
                await self._check_server_type_tasks()

            except asyncio.CancelledError:
                break
            except Exception as e:
                log.exception("Exception in recovery loop: {}", e)

    async def _check_server_tasks(self) -> None:
        server_tasks = await self._registry.get_server_tasks(self._server_id.server_id)
        heartbeats = await self._registry.get_heartbeats(list(server_tasks))
        for task_id, timestamp in heartbeats.items():
            if self._should_retry(timestamp):
                metadata = await self._registry.get_task(task_id)
                if metadata is None:
                    log.warning("Task {} metadata not found, skipping retry", task_id)
                    continue
                task = await self._retry_task(metadata)
                self._bg_ongoing_tasks[task_id] = task

    async def _check_server_type_tasks(self) -> None:
        """Check tasks for a specific server type"""
        server_tasks = await self._registry.get_server_type_tasks(self._server_id.server_type)
        heartbeats = await self._registry.get_heartbeats(list(server_tasks))
        for task_id, timestamp in heartbeats.items():
            if self._should_retry(timestamp):
                metadata = await self._registry.get_task(task_id)
                if metadata is None:
                    log.warning("Task {} metadata not found, skipping retry", task_id)
                    continue
                task = await self._retry_task(metadata)
                self._bg_ongoing_tasks[task_id] = task

    def _should_retry(
        self,
        task_timestamp: float,
        ttl_seconds: float = DEFAULT_TASK_RETRY_TTL,
        current_time: Optional[float] = None,
    ) -> bool:
        """Check if a task is stale and should be retried"""
        now = current_time or time.time()
        return now - task_timestamp > ttl_seconds

    async def _retry_task(self, task: BackgroundTaskMetadata) -> asyncio.Task:
        """Retry a background task"""

        # Update task for retry
        task.update_for_retry()
        task.server_id = self._server_id.server_id  # Claim the task
        await self._registry.update_task(task)

        async def func() -> None:
            # TODO: Implement actual task handling logic
            return

        return asyncio.create_task(func())  # Placeholder for actual task handler
