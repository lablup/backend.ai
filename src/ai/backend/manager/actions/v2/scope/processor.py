import logging
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.actions.run_status import ActionRunStatus
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.log_context import with_scope_action_context
from ai.backend.manager.actions.v2.scope.monitor.base import ScopeActionMonitor
from ai.backend.manager.actions.v2.scope.result import (
    BaseScopeActionResult,
    ScopeActionProcessResult,
    ScopeActionResultMeta,
)
from ai.backend.manager.actions.v2.scope.validator.base import ScopeActionValidator
from ai.backend.manager.actions.v2.trigger import ActionTriggerMeta

__all__ = ("ScopeActionProcessor",)

log = StructuredLogger(logging.getLogger(__spec__.name))


class ScopeActionProcessor[TAction: BaseScopeAction, TResult: BaseScopeActionResult]:
    """Validate, run monitors around, then execute a scope action.

    Each registered validator runs first. The action function then executes within a
    monitor lifecycle: every monitor's ``prepare`` is called before, and ``done`` after
    (on success or failure), with status / timing / error captured into a
    :class:`ScopeActionProcessResult`. This path depends only on the pure-ABC
    :class:`BaseScopeAction`, never on the legacy ``BaseAction`` framework.
    """

    _func: Callable[[TAction], Awaitable[TResult]]
    _monitors: Sequence[ScopeActionMonitor]
    _validators: Sequence[ScopeActionValidator[TAction]]

    def __init__(
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        monitors: Sequence[ScopeActionMonitor] | None = None,
        validators: Sequence[ScopeActionValidator[TAction]] | None = None,
    ) -> None:
        self._func = func
        self._monitors = monitors or []
        self._validators = validators or []

    async def _prepare_monitors(self, action: TAction, trigger_meta: ActionTriggerMeta) -> None:
        for monitor in self._monitors:
            try:
                await monitor.prepare(action, trigger_meta)
            except Exception as e:
                log.warning("action monitor prepare failed", exc_info=e)

    async def _finalize_monitors(self, action: TAction, meta: ScopeActionResultMeta) -> None:
        process_result = ScopeActionProcessResult(meta=meta)
        for monitor in reversed(self._monitors):
            try:
                await monitor.done(action, process_result)
            except Exception as e:
                log.warning("action monitor done failed", exc_info=e)

    async def run(self, action: TAction) -> TResult:
        with with_scope_action_context(action) as action_id:
            started_at = datetime.now(UTC)
            trigger_meta = ActionTriggerMeta(action_id=action_id, started_at=started_at)

            run_status = ActionRunStatus.unknown()
            entity_ids: Sequence[EntityIdentifier] = []

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
                    entity_ids = result.entity_ids()
                    run_status = ActionRunStatus.success()
                    return result
            finally:
                ended_at = datetime.now(UTC)
                meta = ScopeActionResultMeta(
                    action_id=action_id,
                    scope_targets=action.scope_targets(),
                    entity_ids=entity_ids,
                    status=run_status.status,
                    description=run_status.description,
                    started_at=started_at,
                    ended_at=ended_at,
                    duration=ended_at - started_at,
                    error_code=run_status.error_code,
                )
                await self._finalize_monitors(action, meta)
