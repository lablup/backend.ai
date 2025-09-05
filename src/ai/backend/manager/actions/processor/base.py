import logging
import uuid
from datetime import datetime
from typing import Awaitable, Callable, Generic, Optional

from ai.backend.common.exception import BackendAIError, ErrorCode
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.actions.validator.base import ActionValidator

from ..action import (
    BaseActionResultMeta,
    BaseActionTriggerMeta,
    ProcessResult,
    TAction,
    TActionResult,
)
from ..monitors.monitor import ActionMonitor

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ActionRunner(Generic[TAction, TActionResult]):
    _func: Callable[[TAction], Awaitable[TActionResult]]
    _monitors: list[ActionMonitor]

    def __init__(
        self,
        func: Callable[[TAction], Awaitable[TActionResult]],
        monitors: Optional[list[ActionMonitor]],
    ) -> None:
        self._func = func
        self._monitors = monitors or []

    async def _start_monitors(
        self, action: TAction, action_trigger_meta: BaseActionTriggerMeta
    ) -> None:
        for monitor in self._monitors:
            try:
                await monitor.prepare(action, action_trigger_meta)
            except Exception as e:
                log.warning("Error in monitor prepare method: {}", e)

    async def _finalize_monitors(
        self,
        action: TAction,
        meta: BaseActionResultMeta,
    ) -> None:
        process_result = ProcessResult(meta=meta)
        for monitor in reversed(self._monitors):
            try:
                await monitor.done(action, process_result)
            except Exception as e:
                log.warning("Error in monitor done method: {}", e)

    async def run(
        self, action: TAction, action_trigger_meta: BaseActionTriggerMeta
    ) -> TActionResult:
        started_at = action_trigger_meta.started_at
        action_id = action_trigger_meta.action_id
        status = OperationStatus.UNKNOWN
        description: str = "unknown"
        result: Optional[TActionResult] = None
        error_code: Optional[ErrorCode] = None

        await self._start_monitors(action, action_trigger_meta)
        try:
            result = await self._func(action)
        except BackendAIError as e:
            log.exception("Action processing error: {}", e)
            status = OperationStatus.ERROR
            description = str(e)
            error_code = e.error_code()
            raise
        except BaseException as e:
            log.exception("Unexpected error during action processing: {}", e)
            status = OperationStatus.ERROR
            description = str(e)
            error_code = ErrorCode.default()
            raise
        else:
            status = OperationStatus.SUCCESS
            description = "Success"
            return result
        finally:
            entity_id = action.entity_id()
            if entity_id is None and result is not None:
                entity_id = result.entity_id()
            ended_at = datetime.now()
            duration = ended_at - started_at
            meta = BaseActionResultMeta(
                action_id=action_id,
                entity_id=entity_id,
                status=status,
                description=description,
                started_at=started_at,
                ended_at=ended_at,
                duration=duration,
                error_code=error_code,
            )
            await self._finalize_monitors(
                action,
                meta,
            )


class ActionProcessor(Generic[TAction, TActionResult]):
    _validators: list[ActionValidator]

    _runner: ActionRunner[TAction, TActionResult]

    def __init__(
        self,
        func: Callable[[TAction], Awaitable[TActionResult]],
        monitors: Optional[list[ActionMonitor]] = None,
        validators: Optional[list[ActionValidator]] = None,
    ) -> None:
        self._runner = ActionRunner(func, monitors)

        self._validators = validators or []

    async def _run(self, action: TAction) -> TActionResult:
        started_at = datetime.now()
        action_id = uuid.uuid4()
        action_trigger_meta = BaseActionTriggerMeta(action_id=action_id, started_at=started_at)
        for validator in self._validators:
            await validator.validate(action, action_trigger_meta)

        return await self._runner.run(action, action_trigger_meta)

    async def wait_for_complete(self, action: TAction) -> TActionResult:
        return await self._run(action)
