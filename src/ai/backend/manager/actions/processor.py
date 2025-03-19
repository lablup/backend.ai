import uuid
from abc import ABC
from datetime import datetime
from typing import Awaitable, Callable, Generic, Optional

from ai.backend.common.bgtask import BackgroundTaskManager, ProgressReporter
from ai.backend.common.types import DispatchResult

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

    async def _run(self, action: TAction) -> TActionResult:
        started_at = datetime.now()
        status: str = "unknown"
        description: str = "unknown"
        result: Optional[TActionResult] = None
        for monitor in self._monitors:
            await monitor.prepare(action)
        try:
            result = await self._func(action)
            status = "success"
            description = "Success"
        except BaseException as e:
            status = "error"
            description = str(e)
            raise
        finally:
            end_at = datetime.now()
            duration = (end_at - started_at).total_seconds()
            meta = BaseActionResultMeta(
                status=status,
                description=description,
                started_at=started_at,
                end_at=end_at,
                duration=duration,
            )
            process_result = ProcessResult(meta=meta, result=result)
            for monitor in reversed(self._monitors):
                await monitor.done(action, process_result)
        return result

    async def wait_for_complete(self, action: TAction) -> TActionResult:
        return await self._run(action)

    async def fire_and_forget(
        self, background_task_manager: BackgroundTaskManager, action: TAction
    ) -> uuid.UUID:
        async def _bg_task(reporter: ProgressReporter) -> DispatchResult:
            result = await self.wait_for_complete(action)
            return result.to_bgtask_result()

        return await background_task_manager.start(_bg_task)
