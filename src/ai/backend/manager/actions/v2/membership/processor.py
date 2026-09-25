import logging
import uuid
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.run_status import ActionRunStatus
from ai.backend.manager.actions.v2.membership.base import BaseMembershipAction
from ai.backend.manager.actions.v2.membership.monitor.base import MembershipActionMonitor
from ai.backend.manager.actions.v2.membership.result import (
    MembershipActionProcessResult,
    MembershipActionResultMeta,
)
from ai.backend.manager.actions.v2.membership.trigger import MembershipActionTriggerMeta
from ai.backend.manager.actions.v2.membership.validator.base import MembershipActionValidator

__all__ = ("MembershipActionProcessor",)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class MembershipActionProcessor[TAction: BaseMembershipAction, TResult]:
    """Validate, run monitors around, then move the entity. A denial ends the run."""

    _func: Callable[[TAction], Awaitable[TResult]]
    _monitors: Sequence[MembershipActionMonitor]
    _validators: Sequence[MembershipActionValidator]

    def __init__(
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        monitors: Sequence[MembershipActionMonitor] | None = None,
        validators: Sequence[MembershipActionValidator] | None = None,
    ) -> None:
        self._func = func
        self._monitors = monitors or []
        self._validators = validators or []

    async def _prepare_monitors(self, trigger_meta: MembershipActionTriggerMeta) -> None:
        for monitor in self._monitors:
            try:
                await monitor.prepare(trigger_meta)
            except Exception as e:
                log.warning("Error in monitor prepare method: {}", e)

    async def _finalize_monitors(
        self, trigger_meta: MembershipActionTriggerMeta, meta: MembershipActionResultMeta
    ) -> None:
        process_result = MembershipActionProcessResult(meta=meta)
        for monitor in reversed(self._monitors):
            try:
                await monitor.done(trigger_meta, process_result)
            except Exception as e:
                log.warning("Error in monitor done method: {}", e)

    async def run(self, action: TAction) -> TResult:
        started_at = datetime.now(UTC)
        trigger_meta = MembershipActionTriggerMeta(
            action_id=uuid.uuid4(),
            started_at=started_at,
            entity=action.entity(),
            scopes=action.scopes(),
            operation_type=action.operation_type(),
            action_name=action.action_name(),
        )

        run_status = ActionRunStatus.unknown()

        await self._prepare_monitors(trigger_meta)
        try:
            try:
                for validator in self._validators:
                    await validator.validate(trigger_meta)
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
            meta = MembershipActionResultMeta(
                status=run_status.status,
                description=run_status.description,
                ended_at=ended_at,
                duration=ended_at - started_at,
                error_code=run_status.error_code,
            )
            await self._finalize_monitors(trigger_meta, meta)
