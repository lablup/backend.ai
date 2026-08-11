import logging
import uuid
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.run_status import ActionRunStatus
from ai.backend.manager.actions.v2.lookup.base import BaseLookupAction, BaseLookupActionResult
from ai.backend.manager.actions.v2.lookup.monitor import LookupActionMonitor
from ai.backend.manager.actions.v2.lookup.result import (
    LookupActionProcessResult,
    LookupActionResultMeta,
)
from ai.backend.manager.actions.v2.lookup.validator import (
    AuthenticatedActionValidator,
    LookupActionValidator,
)

__all__ = ("LookupActionProcessor",)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class LookupActionProcessor[TAction: BaseLookupAction, TResult: BaseLookupActionResult]:
    """Validate, run monitors around, then execute a lookup action.

    The authentication gate always runs first — it is the whole of this layer's
    authorization, since a lookup has no target to check permissions against.
    """

    _func: Callable[[TAction], Awaitable[TResult]]
    _monitors: Sequence[LookupActionMonitor]
    _validators: Sequence[LookupActionValidator]

    def __init__(
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        monitors: Sequence[LookupActionMonitor] | None = None,
        validators: Sequence[LookupActionValidator] | None = None,
    ) -> None:
        self._func = func
        self._monitors = monitors or []
        self._validators = [AuthenticatedActionValidator(), *(validators or [])]

    async def _prepare_monitors(self, action: TAction, trigger_meta: BaseActionTriggerMeta) -> None:
        for monitor in self._monitors:
            try:
                await monitor.prepare(action, trigger_meta)
            except Exception as e:
                log.warning("Error in monitor prepare method: {}", e)

    async def _finalize_monitors(self, action: TAction, meta: LookupActionResultMeta) -> None:
        process_result = LookupActionProcessResult(meta=meta)
        for monitor in reversed(self._monitors):
            try:
                await monitor.done(action, process_result)
            except Exception as e:
                log.warning("Error in monitor done method: {}", e)

    async def run(self, action: TAction) -> TResult:
        started_at = datetime.now(UTC)
        action_id = uuid.uuid4()
        trigger_meta = BaseActionTriggerMeta(action_id=action_id, started_at=started_at)

        run_status = ActionRunStatus.unknown()

        # Validation runs inside the monitor lifecycle so a rejected action is
        # recorded too; monitors that only wrapped execution missed every denial.
        await self._prepare_monitors(action, trigger_meta)
        try:
            try:
                for validator in self._validators:
                    await validator.validate(action, trigger_meta)
            except BaseException as e:
                run_status = ActionRunStatus.of_failure(e, during_validation=True)
                raise
            try:
                result = await self._func(action)
            except BaseException as e:
                run_status = ActionRunStatus.of_failure(e, during_validation=False)
                raise
            else:
                run_status = ActionRunStatus.success()
                return result
        finally:
            ended_at = datetime.now(UTC)
            meta = LookupActionResultMeta(
                action_id=action_id,
                status=run_status.status,
                description=run_status.description,
                started_at=started_at,
                ended_at=ended_at,
                duration=ended_at - started_at,
                error_code=run_status.error_code,
            )
            await self._finalize_monitors(action, meta)
