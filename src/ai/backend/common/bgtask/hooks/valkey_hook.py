from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from ...clients.valkey_client.valkey_bgtask.client import TaskSetKey, ValkeyBgtaskClient
from .base import AbstractTaskHook, TaskContext


class ValkeyUnregisterHook(AbstractTaskHook):
    """Hook for unregistering task from Valkey after completion."""

    def __init__(
        self,
        valkey_client: ValkeyBgtaskClient,
        task_set_key: TaskSetKey,
    ):
        self._valkey_client = valkey_client
        self._task_set_key = task_set_key

    @asynccontextmanager
    async def apply(self, context: TaskContext) -> AsyncIterator[TaskContext]:
        try:
            yield context
        finally:
            # Post-execution: unregister task using task_id from context
            await self._valkey_client.unregister_task(context.task_id, self._task_set_key)
