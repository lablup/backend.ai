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
from ai.backend.manager.actions.validators.validator.batch import BatchActionValidator

from ..action.batch import (
    TBaseBatchAction,
    TBaseBatchActionResult,
)
from ..monitors.monitor.base import ActionMonitor

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class BatchActionProcessor(Generic[TBaseBatchAction, TBaseBatchActionResult]):
    _monitors: list[ActionMonitor]
    _validators: list[BatchActionValidator]
    _func: Callable[[TBaseBatchAction], Awaitable[TBaseBatchActionResult]]

    def __init__(
        self,
        func: Callable[[TBaseBatchAction], Awaitable[TBaseBatchActionResult]],
        monitors: Optional[list[ActionMonitor]] = None,
        validators: Optional[list[BatchActionValidator]] = None,
    ) -> None:
        self._func = func
        self._monitors = monitors or []
        self._validators = validators or []

    async def _run(self, action: TBaseBatchAction) -> TBaseBatchActionResult:
        started_at = datetime.now()
        status = OperationStatus.UNKNOWN
        description: str = "unknown"
        result: Optional[TBaseBatchActionResult] = None
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
            entity_ids = action.target_entity_ids()
            if not entity_ids and result is not None:
                entity_ids = result.entity_ids()
            meta = ActionResultMeta(
                action_id=action_id,
                target=ActionResultTargetMeta(
                    entity_type=action.entity_type(),
                    entity_ids=entity_ids,
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

    async def wait_for_complete(self, action: TBaseBatchAction) -> TBaseBatchActionResult:
        return await self._run(action)
