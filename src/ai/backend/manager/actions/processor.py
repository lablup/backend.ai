import asyncio
from datetime import datetime
from typing import Generic, TypeVar

from .middlewares.middleware import ActionMonitor
from .action import BaseAction, BaseActionResult, BaseActionResultMeta, ProcessResult


TAction = TypeVar("TAction", bound=BaseAction)
TActionResult = TypeVar("TActionResult", bound=BaseActionResult)


class ActionProcessor(Generic[TAction, TActionResult]):
    _monitors: list[ActionMonitor]
    _func: callable[[TAction], TActionResult]

    def __init__(self, func: callable[[TAction], TActionResult], monitors: list[ActionMonitor] = None) -> None:
        self._func = func
        self._monitors = monitors or []
    
    async def _run(self, action: TAction) -> ProcessResult:
        started_at = datetime.now()
        status: str
        try:
            result = self._func(action)
            status = "success"
            description = "Success"
        except Exception as e:
            status = "error"
            description = str(e)
        finally:
            end_at = datetime.now()
            duration = (end_at - started_at).total_seconds()
            meta = BaseActionResultMeta(
                status=status,
                description=description,
                started_at=started_at,
                end_at=end_at,
                duration=duration
            )
            return ProcessResult(meta, result)
    
    async def wait_for_complete(self, action: TAction) -> TActionResult:
        for monitor in self._monitors:
            await monitor.prepare(action)
        result = await self._run(action)
        for monitor in reversed(self._monitors):
            await monitor.done(action, result)
        return result
    
    async def fire_and_forget(self, action: TAction) -> None:
        asyncio.create_task(self.wait_for_complete(action))
