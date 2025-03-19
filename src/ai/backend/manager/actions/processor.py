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

    # TODO: background_task_manager를 ActionProcessor 생성자에서 받아오는 게 나은지?
    async def fire_and_forget(
        self, background_task_manager: BackgroundTaskManager, action: TAction
    ) -> uuid.UUID:
        async def _bg_task(reporter: ProgressReporter) -> DispatchResult:
            result = await self.wait_for_complete(action)
            return result.to_bgtask_result()

        return await background_task_manager.start(_bg_task)
