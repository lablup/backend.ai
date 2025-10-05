from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, Optional

from ..task_result import TaskResult
from ..types import TaskID, TaskName


@dataclass
class TaskContext:
    """Context object that holds task execution information."""

    task_name: TaskName
    task_id: TaskID
    result: Optional[TaskResult] = None


class AbstractTaskHook(ABC):
    """Abstract base class for task execution hooks."""

    @abstractmethod
    @asynccontextmanager
    async def apply(self, context: TaskContext) -> AsyncIterator[TaskContext]:
        """
        Context manager for task execution hooks.
        Pre-execution logic runs before yield.
        Post-execution logic runs after yield.
        The context.result will be populated after task execution.
        Yields the context object that can be modified during execution.
        """
        raise NotImplementedError("Subclasses must implement this method")
        yield context  # type: ignore
