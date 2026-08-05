import logging
import uuid
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.run_status import ActionRunStatus
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.bulk.monitor import BulkActionMonitor
from ai.backend.manager.actions.v2.bulk.result import (
    BaseBulkActionResult,
    BulkActionProcessResult,
    BulkActionResultMeta,
    BulkEntityResult,
)
from ai.backend.manager.actions.v2.bulk.validator import BulkActionValidator

__all__ = ("BulkActionProcessor",)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class BulkActionProcessor[TAction: BaseBulkAction, TResult: BaseBulkActionResult]:
    """Validate, run monitors around, then execute a bulk action.

    Each registered validator runs first. The action function then executes within a
    monitor lifecycle: every monitor's ``prepare`` is called before, and ``done`` after
    (on success or failure), with status / timing / error captured into a
    :class:`BulkActionProcessResult`. This path depends only on the pure-ABC
    :class:`BaseBulkAction`, never on the legacy ``BaseAction`` framework.
    """

    _func: Callable[[TAction], Awaitable[TResult]]
    _monitors: Sequence[BulkActionMonitor]
    _validators: Sequence[BulkActionValidator]

    def __init__(
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        monitors: Sequence[BulkActionMonitor] | None = None,
        validators: Sequence[BulkActionValidator] | None = None,
    ) -> None:
        self._func = func
        self._monitors = monitors or []
        self._validators = validators or []

    async def _prepare_monitors(self, action: TAction, trigger_meta: BaseActionTriggerMeta) -> None:
        for monitor in self._monitors:
            try:
                await monitor.prepare(action, trigger_meta)
            except Exception as e:
                log.warning("Error in monitor prepare method: {}", e)

    async def _finalize_monitors(self, action: TAction, meta: BulkActionResultMeta) -> None:
        process_result = BulkActionProcessResult(meta=meta)
        for monitor in reversed(self._monitors):
            try:
                await monitor.done(action, process_result)
            except Exception as e:
                log.warning("Error in monitor done method: {}", e)

    async def run(self, action: TAction) -> TResult:
        started_at = datetime.now(UTC)
        action_id = uuid.uuid4()
        trigger_meta = BaseActionTriggerMeta(action_id=action_id, started_at=started_at)

        entity_results: Sequence[BulkEntityResult] = []

        # Validation runs inside the monitor lifecycle so a rejected action is
        # recorded too; monitors that only wrapped execution missed every denial.
        await self._prepare_monitors(action, trigger_meta)
        try:
            try:
                for validator in self._validators:
                    await validator.validate(action, trigger_meta)
            except BaseException as e:
                run_status = ActionRunStatus.of_failure(e, during_validation=True)
                entity_results = self._same_result_for_every_entity(action, run_status)
                raise
            try:
                result = await self._func(action)
            except BaseException as e:
                run_status = ActionRunStatus.of_failure(e, during_validation=False)
                entity_results = self._same_result_for_every_entity(action, run_status)
                raise
            else:
                entity_results = result.entity_results()
                return result
        finally:
            ended_at = datetime.now(UTC)
            meta = BulkActionResultMeta(
                action_id=action_id,
                entity_results=entity_results,
                started_at=started_at,
                ended_at=ended_at,
                duration=ended_at - started_at,
            )
            await self._finalize_monitors(action, meta)

    def _same_result_for_every_entity(
        self, action: TAction, run_status: ActionRunStatus
    ) -> Sequence[BulkEntityResult]:
        """Attribute a whole-run failure to every entity the caller named."""
        return [
            BulkEntityResult(
                entity_id=entity_id,
                status=run_status.status,
                description=run_status.description,
                error_code=run_status.error_code,
            )
            for entity_id in action.entity_ids()
        ]
