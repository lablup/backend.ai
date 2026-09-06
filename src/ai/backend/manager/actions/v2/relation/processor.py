import logging
import uuid
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.run_status import ActionRunStatus
from ai.backend.manager.actions.v2.relation.base import BaseRelationAction
from ai.backend.manager.actions.v2.relation.monitor import RelationActionMonitor
from ai.backend.manager.actions.v2.relation.result import (
    RelationActionProcessResult,
    RelationActionResultMeta,
)
from ai.backend.manager.actions.v2.relation.trigger import RelationActionTriggerMeta
from ai.backend.manager.actions.v2.relation.validator import RelationActionValidator

__all__ = ("RelationActionProcessor",)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RelationActionProcessor[TAction: BaseRelationAction, TResult]:
    """Validate, run monitors around, then link or unlink.

    The same lifecycle every v2 shape runs. There is nothing to narrow — the row is
    about both scopes — so a denial ends the run.
    """

    _func: Callable[[TAction], Awaitable[TResult]]
    _monitors: Sequence[RelationActionMonitor]
    _validators: Sequence[RelationActionValidator]

    def __init__(
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        monitors: Sequence[RelationActionMonitor] | None = None,
        validators: Sequence[RelationActionValidator] | None = None,
    ) -> None:
        self._func = func
        self._monitors = monitors or []
        self._validators = validators or []

    async def _prepare_monitors(self, trigger_meta: RelationActionTriggerMeta) -> None:
        for monitor in self._monitors:
            try:
                await monitor.prepare(trigger_meta)
            except Exception as e:
                log.warning("Error in monitor prepare method: {}", e)

    async def _finalize_monitors(
        self, trigger_meta: RelationActionTriggerMeta, meta: RelationActionResultMeta
    ) -> None:
        process_result = RelationActionProcessResult(meta=meta)
        for monitor in reversed(self._monitors):
            try:
                await monitor.done(trigger_meta, process_result)
            except Exception as e:
                log.warning("Error in monitor done method: {}", e)

    async def run(self, action: TAction) -> TResult:
        started_at = datetime.now(UTC)
        trigger_meta = RelationActionTriggerMeta(
            action_id=uuid.uuid4(),
            started_at=started_at,
            scope_targets=action.scope_targets(),
            operation_type=action.operation_type(),
            action_name=action.action_name(),
        )

        run_status = ActionRunStatus.unknown()

        # Validation runs inside the monitor lifecycle so a rejected action is
        # recorded too; monitors that only wrapped execution missed every denial.
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
            meta = RelationActionResultMeta(
                status=run_status.status,
                description=run_status.description,
                ended_at=ended_at,
                duration=ended_at - started_at,
                error_code=run_status.error_code,
            )
            await self._finalize_monitors(trigger_meta, meta)
