import logging
import uuid
from datetime import datetime
from typing import Awaitable, Callable, Generic, Optional

from ai.backend.common.exception import BackendAIError, ErrorCode
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.types import ActionTriggerMeta, OperationStatus, ProcessResult
from ai.backend.manager.actions.validators.validator import ActionValidator
from ai.backend.manager.data.permission.id import (
    ObjectId,
)
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)

from ..action.scope import (
    TBaseScopeAction,
    TBaseScopeActionResult,
)
from ..monitors.monitor import ActionMonitor

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ActionProcessor(Generic[TBaseScopeAction, TBaseScopeActionResult]):
    _monitors: list[ActionMonitor]
    _validators: list[ActionValidator]
    _repository: PermissionControllerRepository
    _func: Callable[[TBaseScopeAction], Awaitable[TBaseScopeActionResult]]

    def __init__(
        self,
        func: Callable[[TBaseScopeAction], Awaitable[TBaseScopeActionResult]],
        permission_control_repository: PermissionControllerRepository,
        monitors: Optional[list[ActionMonitor]] = None,
        validators: Optional[list[ActionValidator]] = None,
    ) -> None:
        self._func = func
        self._monitors = monitors or []
        self._validators = validators or []
        self._repository = permission_control_repository

    async def _run(self, action: TBaseScopeAction) -> TBaseScopeActionResult:
        started_at = datetime.now()
        status = OperationStatus.UNKNOWN
        description: str = "unknown"
        result: Optional[TBaseScopeActionResult] = None
        error_code: Optional[ErrorCode] = None
        object_ids: list[ObjectId] = []

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
            meta = BaseScopeActionResultMeta(
                action_id=action_id,
                scope_id=action.scope_id(),
                accessible_entity_ids=object_ids,
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

    async def wait_for_complete(self, action: TBaseScopeAction) -> TBaseScopeActionResult:
        return await self._run(action)
