import asyncio
from abc import ABC
from datetime import datetime
from typing import Awaitable, Callable, Generic, Optional

from .action import (
    BaseAction,
    BaseActionResultMeta,
    ProcessResult,
    TAction,
    TActionResult,
)
from .monitors.monitor import ActionMonitor


class ActionValidator(ABC):
    async def validate(self, action: BaseAction) -> None:
        pass


class ActionProcessor(Generic[TAction, TActionResult]):
    _monitors: list[ActionMonitor]
    _func: Callable[[TAction], Awaitable[TActionResult]]

    def __init__(
        self,
        func: Callable[[TAction], Awaitable[TActionResult]],
        monitors: Optional[list[ActionMonitor]] = None,
    ) -> None:
        self._func = func
        self._monitors = monitors or []

    async def _run(self, action: TAction) -> ProcessResult[TActionResult]:
        started_at = datetime.now()
        status: str
        exc: Optional[Exception] = None
        try:
            result = await self._func(action)
            status = "success"
            description = "Success"
        except Exception as e:
            exc = e
            result = None
            status = "error"
            description = str(e)

        end_at = datetime.now()
        duration = (end_at - started_at).total_seconds()
        meta = BaseActionResultMeta(
            status=status,
            description=description,
            started_at=started_at,
            end_at=end_at,
            duration=duration,
        )

        if result:
            return ProcessResult(meta, result)
        else:
            assert exc is not None
            raise exc

    async def wait_for_complete(self, action: TAction) -> TActionResult:
        for monitor in self._monitors:
            await monitor.prepare(action)
        result = await self._run(action)
        for monitor in reversed(self._monitors):
            await monitor.done(action, result)
        return result.result

    async def fire_and_forget(self, action: TAction) -> None:
        asyncio.create_task(self.wait_for_complete(action))
