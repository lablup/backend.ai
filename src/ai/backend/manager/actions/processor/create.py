import logging
import uuid
from datetime import datetime
from typing import Awaitable, Callable, Generic, Optional

from ai.backend.common.exception import BackendAIError, ErrorCode
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.callbacks.callback.create import CreateActionCallback
from ai.backend.manager.actions.types import (
    ActionResultMeta,
    ActionResultTargetMeta,
    ActionTriggerMeta,
    OperationStatus,
    ProcessResult,
)
from ai.backend.manager.actions.validators.validator.create import CreateActionValidator

from ..action.create import (
    TBaseCreateAction,
    TBaseCreateActionResult,
)
from ..monitors.monitor.base import ActionMonitor

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class CreateActionProcessor(Generic[TBaseCreateAction, TBaseCreateActionResult]):
    _monitors: list[ActionMonitor]
    _validators: list[CreateActionValidator]
    _callbacks: list[CreateActionCallback]
    _func: Callable[[TBaseCreateAction], Awaitable[TBaseCreateActionResult]]

    def __init__(
        self,
        func: Callable[[TBaseCreateAction], Awaitable[TBaseCreateActionResult]],
        monitors: Optional[list[ActionMonitor]] = None,
        validators: Optional[list[CreateActionValidator]] = None,
        callbacks: Optional[list[CreateActionCallback]] = None,
    ) -> None:
        self._func = func
        self._monitors = monitors or []
        self._validators = validators or []
        self._callbacks = callbacks or []

    async def _run(self, action: TBaseCreateAction) -> TBaseCreateActionResult:
        started_at = datetime.now()
        status = OperationStatus.UNKNOWN
        description: str = "unknown"
        result: Optional[TBaseCreateActionResult] = None
        error_code: Optional[ErrorCode] = None

        action_id = uuid.uuid4()
        action_trigger_meta = ActionTriggerMeta(action_id=action_id, started_at=started_at)
        for monitor in self._monitors:
            try:
                await monitor.prepare(action, action_trigger_meta)
            except Exception as e:
                log.warning("Error in monitor prepare method: {}", e)
        try:
            for validator in self._validators:
                await validator.validate(action, action_trigger_meta)
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
        else:
            for callback in self._callbacks:
                await callback.callback(result)
        finally:
            ended_at = datetime.now()
            duration = ended_at - started_at
            meta = ActionResultMeta(
                action_id=action_id,
                target=ActionResultTargetMeta(
                    entity_type=action.entity_type(),
                ),
                status=status,
                description=description,
                started_at=started_at,
                ended_at=ended_at,
                duration=duration,
                error_code=error_code,
            )
            process_result = ProcessResult(meta=meta)
            for monitor in reversed(self._monitors):
                try:
                    await monitor.done(action, process_result)
                except Exception as e:
                    log.warning("Error in monitor done method: {}", e)
        return result

    async def wait_for_complete(self, action: TBaseCreateAction) -> TBaseCreateActionResult:
        return await self._run(action)
