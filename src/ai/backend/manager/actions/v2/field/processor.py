import logging
import uuid
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime
from typing import Any

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.run_status import ActionRunStatus
from ai.backend.manager.actions.v2.field.base import BaseSingleFieldAction
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import FieldOwnerLookupOpsResult
from ai.backend.manager.actions.v2.single_entity.monitor import SingleEntityActionMonitor
from ai.backend.manager.actions.v2.single_entity.result import (
    SingleEntityActionProcessResult,
    SingleEntityActionResultMeta,
)
from ai.backend.manager.actions.v2.single_entity.trigger import SingleEntityActionTriggerMeta
from ai.backend.manager.actions.v2.single_entity.validator import SingleEntityActionValidator

__all__ = ("SingleFieldActionProcessor",)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

type OwnerLookupProcessor = LookupActionProcessor[
    LookupFieldOwnerOpsAction[Any, Any], FieldOwnerLookupOpsResult
]


class SingleFieldActionProcessor[TAction: BaseSingleFieldAction[Any, Any], TResult]:
    """Look the field row's owner up, then run the single-entity pipeline against it.

    Two runs, each recorded as what it is: a lookup reading the entity that owns the
    row, then the operation authorized and audited against that entity. The validators
    and monitors are the single-entity ones, unchanged.

    A field row that is gone ends at the lookup, which already answers a miss exactly as
    it answers a denial.
    """

    _func: Callable[[TAction], Awaitable[TResult]]
    _owner_lookup: OwnerLookupProcessor
    _monitors: Sequence[SingleEntityActionMonitor]
    _validators: Sequence[SingleEntityActionValidator]

    def __init__(
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        owner_lookup: OwnerLookupProcessor,
        monitors: Sequence[SingleEntityActionMonitor] | None = None,
        validators: Sequence[SingleEntityActionValidator] | None = None,
    ) -> None:
        self._func = func
        self._owner_lookup = owner_lookup
        self._monitors = monitors or []
        self._validators = validators or []

    async def _prepare_monitors(self, trigger_meta: SingleEntityActionTriggerMeta) -> None:
        for monitor in self._monitors:
            try:
                await monitor.prepare(trigger_meta)
            except Exception as e:
                log.warning("Error in monitor prepare method: {}", e)

    async def _finalize_monitors(
        self, trigger_meta: SingleEntityActionTriggerMeta, meta: SingleEntityActionResultMeta
    ) -> None:
        process_result = SingleEntityActionProcessResult(meta=meta)
        for monitor in reversed(self._monitors):
            try:
                await monitor.done(trigger_meta, process_result)
            except Exception as e:
                log.warning("Error in monitor done method: {}", e)

    async def run(self, action: TAction) -> TResult:
        lookup_result = await self._owner_lookup.run(action.to_owner_lookup_action())

        started_at = datetime.now(UTC)
        trigger_meta = SingleEntityActionTriggerMeta(
            action_id=uuid.uuid4(),
            started_at=started_at,
            entity=lookup_result.owner_entity_id.entity_ref(),
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
            meta = SingleEntityActionResultMeta(
                status=run_status.status,
                description=run_status.description,
                ended_at=ended_at,
                duration=ended_at - started_at,
                error_code=run_status.error_code,
            )
            await self._finalize_monitors(trigger_meta, meta)
