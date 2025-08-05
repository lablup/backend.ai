import logging
import uuid
from datetime import datetime
from typing import Awaitable, Callable, Generic, Optional

from ai.backend.common.exception import BackendAIError, ErrorCode
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.types import (
    ActionResultMeta,
    ActionResultTargetMeta,
    ActionTriggerMeta,
    OperationStatus,
    ProcessResult,
)
from ai.backend.manager.actions.validators.validator.scope import ScopedActionValidator
from ai.backend.manager.data.permission.id import ScopeId

from ..action.scope import (
    TBaseScopedAction,
    TBaseScopedActionResult,
)
from ..monitors.monitor.base import ActionMonitor

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ScopedActionProcessor(Generic[TBaseScopedAction, TBaseScopedActionResult]):
    _monitors: list[ActionMonitor]
    _validators: list[ScopedActionValidator]
    _func: Callable[[TBaseScopedAction], Awaitable[TBaseScopedActionResult]]

    def __init__(
        self,
        func: Callable[[TBaseScopedAction], Awaitable[TBaseScopedActionResult]],
        monitors: Optional[list[ActionMonitor]] = None,
        validators: Optional[list[ScopedActionValidator]] = None,
    ) -> None:
        self._func = func
        self._monitors = monitors or []
        self._validators = validators or []

    async def _run(self, action: TBaseScopedAction) -> TBaseScopedActionResult:
        started_at = datetime.now()
        status = OperationStatus.UNKNOWN
        description: str = "unknown"
        result: Optional[TBaseScopedActionResult] = None
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
            return result
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
            meta = ActionResultMeta(
                action_id=action_id,
                target=ActionResultTargetMeta(
                    entity_type=action.entity_type(),
                    scope=ScopeId(action.scope_type(), action.scope_id()),
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

    async def wait_for_complete(self, action: TBaseScopedAction) -> TBaseScopedActionResult:
        return await self._run(action)
