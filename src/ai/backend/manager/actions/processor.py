import asyncio
import uuid
from datetime import datetime
from typing import Awaitable, Callable, Generic, Optional

from ai.backend.common.exception import BackendAIError, ErrorCode
from ai.backend.manager.actions.types import OperationStatus

from .action import (
    BaseActionResultMeta,
    BaseActionTriggerMeta,
    ProcessResult,
    TAction,
    TActionResult,
)
from .monitors.monitor import ActionMonitor


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
        status = OperationStatus.UNKNOWN
        description: str = "unknown"
        result: Optional[TActionResult] = None
        error_code: Optional[ErrorCode] = None

        action_id = uuid.uuid4()
        action_trigger_meta = BaseActionTriggerMeta(action_id=action_id, started_at=started_at)
        for monitor in self._monitors:
            await monitor.prepare(action, action_trigger_meta)
        try:
            result = await self._func(action)
            status = OperationStatus.SUCCESS
            description = "Success"
        except BackendAIError as e:
            status = OperationStatus.ERROR
            description = str(e)
            error_code = e.error_code()
            raise
        except BaseException as e:
            status = OperationStatus.ERROR
            description = str(e)
            error_code = ErrorCode.default()
            raise
        finally:
            ended_at = datetime.now()
            duration = ended_at - started_at
            meta = BaseActionResultMeta(
                action_id=action_id,
                status=status,
                description=description,
                started_at=started_at,
                ended_at=ended_at,
                duration=duration,
                error_code=error_code,
            )
            process_result = ProcessResult(meta=meta, result=result)
            for monitor in reversed(self._monitors):
                await monitor.done(action, process_result)
        return result

    async def wait_for_complete(self, action: TAction) -> TActionResult:
        return await self._run(action)

    async def fire_and_forget(self, action: TAction) -> None:
        asyncio.create_task(self.wait_for_complete(action))
