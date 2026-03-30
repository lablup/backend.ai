from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager

from .base import AbstractTaskHook, TaskContext


class CompositeTaskHook(AbstractTaskHook):
    """Composite hook that applies multiple hooks in sequence."""

    def __init__(self, hooks: list[AbstractTaskHook]) -> None:
        self._hooks = hooks

    @asynccontextmanager
    async def apply(self, context: TaskContext) -> AsyncIterator[TaskContext]:
        async with AsyncExitStack() as stack:
            # Apply all hooks in sequence
            for hook in self._hooks:
                context = await stack.enter_async_context(hook.apply(context))

            yield context
