import logging
import uuid
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime

from ai.backend.common.exception import BackendAIError, ErrorCode
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.global_scope.monitor import GlobalActionMonitor
from ai.backend.manager.actions.v2.global_scope.result import (
    GlobalActionProcessResult,
    GlobalActionResultMeta,
)
from ai.backend.manager.actions.v2.global_scope.validator import (
    GlobalActionValidator,
    SuperAdminActionValidator,
)

__all__ = ("GlobalActionProcessor",)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class GlobalActionProcessor[TAction: BaseGlobalAction, TResult]:
    """Validate, run monitors around, then execute a global action.

    The SUPERADMIN gate always runs first — it is the invariant of this layer — then
    any extra validators, then the action within the monitor lifecycle.
    """

    _func: Callable[[TAction], Awaitable[TResult]]
    _monitors: Sequence[GlobalActionMonitor]
    _validators: Sequence[GlobalActionValidator]

    def __init__(
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        monitors: Sequence[GlobalActionMonitor] | None = None,
        validators: Sequence[GlobalActionValidator] | None = None,
    ) -> None:
        self._func = func
        self._monitors = monitors or []
        self._validators = [SuperAdminActionValidator(), *(validators or [])]

    async def _prepare_monitors(self, action: TAction, trigger_meta: BaseActionTriggerMeta) -> None:
        for monitor in self._monitors:
            try:
                await monitor.prepare(action, trigger_meta)
            except Exception as e:
                log.warning("Error in monitor prepare method: {}", e)

    async def _finalize_monitors(self, action: TAction, meta: GlobalActionResultMeta) -> None:
        process_result = GlobalActionProcessResult(meta=meta)
        for monitor in reversed(self._monitors):
            try:
                await monitor.done(action, process_result)
            except Exception as e:
                log.warning("Error in monitor done method: {}", e)

    async def run(self, action: TAction) -> TResult:
        started_at = datetime.now(UTC)
        action_id = uuid.uuid4()
        trigger_meta = BaseActionTriggerMeta(action_id=action_id, started_at=started_at)

        status = OperationStatus.UNKNOWN
        description = "unknown"
        error_code: ErrorCode | None = None

        # Validation runs inside the monitor lifecycle so a rejected action is
        # recorded too; monitors that only wrapped execution missed every denial.
        await self._prepare_monitors(action, trigger_meta)
        try:
            for validator in self._validators:
                await validator.validate(action, trigger_meta)
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
            ended_at = datetime.now(UTC)
            meta = GlobalActionResultMeta(
                action_id=action_id,
                status=status,
                description=description,
                started_at=started_at,
                ended_at=ended_at,
                duration=ended_at - started_at,
                error_code=error_code,
            )
            await self._finalize_monitors(action, meta)
