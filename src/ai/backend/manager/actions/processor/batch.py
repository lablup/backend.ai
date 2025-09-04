import logging
import uuid
from datetime import datetime
from typing import Awaitable, Callable, Generic, Optional

from ai.backend.common.exception import BackendAIError, ErrorCode
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.actions.validator.batch import BatchActionValidator

from ..action import (
    BaseActionResultMeta,
    BaseActionTriggerMeta,
    ProcessResult,
)
from ..action.batch import TBatchAction, TBatchActionResult
from ..monitors.monitor import ActionMonitor

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class BatchActionProcessor(Generic[TBatchAction, TBatchActionResult]):
    _monitors: list[ActionMonitor]
    _validators: list[BatchActionValidator]
    _func: Callable[[TBatchAction], Awaitable[TBatchActionResult]]

    def __init__(
        self,
        func: Callable[[TBatchAction], Awaitable[TBatchActionResult]],
        monitors: Optional[list[ActionMonitor]] = None,
        validators: Optional[list[BatchActionValidator]] = None,
    ) -> None:
        self._func = func
        self._monitors = monitors or []
        self._validators = validators or []

    async def _run(self, action: TBatchAction) -> TBatchActionResult:
        started_at = datetime.now()
        status = OperationStatus.UNKNOWN
        description: str = "unknown"
        result: Optional[TBatchActionResult] = None
        error_code: Optional[ErrorCode] = None

        action_id = uuid.uuid4()
        action_trigger_meta = BaseActionTriggerMeta(action_id=action_id, started_at=started_at)
        for monitor in self._monitors:
            try:
                await monitor.prepare(action, action_trigger_meta)
            except Exception as e:
                log.warning("Error in monitor prepare method: {}", e)
        try:
            for validator in self._validators:
                await validator.validate(action, action_trigger_meta)
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
            ended_at = datetime.now()
            duration = ended_at - started_at
            entity_id = action.entity_id()
            if entity_id is None and result is not None:
                entity_id = result.entity_id()
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
            process_result = ProcessResult(meta=meta)
            for monitor in reversed(self._monitors):
                try:
                    await monitor.done(action, process_result)
                except Exception as e:
                    log.warning("Error in monitor done method: {}", e)

    async def wait_for_complete(self, action: TBatchAction) -> TBatchActionResult:
        return await self._run(action)
