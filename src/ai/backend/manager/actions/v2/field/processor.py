import logging
from collections.abc import Awaitable, Callable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from ai.backend.common.data.entity.types import EntityIdentifier, FieldIdentifier
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.actions.run_status import ActionRunStatus
from ai.backend.manager.actions.v2.bulk.monitor.base import BulkActionMonitor
from ai.backend.manager.actions.v2.bulk.result import (
    BulkActionProcessResult,
    BulkActionResultMeta,
    BulkEntityResult,
)
from ai.backend.manager.actions.v2.bulk.trigger import BulkActionTriggerMeta
from ai.backend.manager.actions.v2.bulk.validator.base import PartialBulkActionValidator
from ai.backend.manager.actions.v2.field.base import (
    BaseNestedFieldSearchAction,
    BaseRuntimeSingleFieldAction,
    BaseSingleFieldAction,
)
from ai.backend.manager.actions.v2.field.log_context import (
    with_nested_field_action_context,
    with_single_field_action_context,
)
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import FieldOwnerLookupOpsResult
from ai.backend.manager.actions.v2.single_entity.monitor.base import SingleEntityActionMonitor
from ai.backend.manager.actions.v2.single_entity.result import (
    SingleEntityActionProcessResult,
    SingleEntityActionResultMeta,
)
from ai.backend.manager.actions.v2.single_entity.trigger import SingleEntityActionTriggerMeta
from ai.backend.manager.actions.v2.single_entity.validator.base import SingleEntityActionValidator
from ai.backend.manager.errors.base.field import FieldNotFoundError

__all__ = ("NestedFieldSearchActionProcessor", "SingleFieldActionProcessor")

log = StructuredLogger(logging.getLogger(__spec__.name))

type OwnerLookupProcessor = LookupActionProcessor[Any, FieldOwnerLookupOpsResult]
"""The step every single-field operation runs first.

Typed on the result rather than the action: which lookup root a row's owner comes from
is the action's business, and both roots answer with the same value.
"""


class SingleFieldActionProcessor[
    TAction: BaseSingleFieldAction[Any, Any] | BaseRuntimeSingleFieldAction[Any],
    TResult,
]:
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
                log.warning("action monitor prepare failed", exc_info=e)

    async def _finalize_monitors(
        self, trigger_meta: SingleEntityActionTriggerMeta, meta: SingleEntityActionResultMeta
    ) -> None:
        process_result = SingleEntityActionProcessResult(meta=meta)
        for monitor in reversed(self._monitors):
            try:
                await monitor.done(trigger_meta, process_result)
            except Exception as e:
                log.warning("action monitor done failed", exc_info=e)

    async def run(self, action: TAction) -> TResult:
        with with_single_field_action_context(action) as action_id:
            lookup_result = await self._owner_lookup.run(action.to_owner_lookup_action())

            started_at = datetime.now(UTC)
            trigger_meta = SingleEntityActionTriggerMeta(
                action_id=action_id,
                started_at=started_at,
                entity=lookup_result.owner_entity_id,
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


class NestedFieldSearchActionProcessor[TAction: BaseNestedFieldSearchAction[Any], TResult]:
    """Read the owners of the field row, then search under it when the caller holds the
    permission on one of them.

    The run is recorded on the first candidate that passed, or, when none did, on the
    first candidate as denied.
    """

    _func: Callable[[TAction], Awaitable[TResult]]
    _owner_candidates: Callable[
        [Sequence[FieldIdentifier]],
        Awaitable[Mapping[FieldIdentifier, Sequence[EntityIdentifier]]],
    ]
    _monitors: Sequence[BulkActionMonitor]
    _validators: Sequence[PartialBulkActionValidator]

    def __init__(
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        owner_candidates: Callable[
            [Sequence[FieldIdentifier]],
            Awaitable[Mapping[FieldIdentifier, Sequence[EntityIdentifier]]],
        ],
        monitors: Sequence[BulkActionMonitor] | None = None,
        validators: Sequence[PartialBulkActionValidator] | None = None,
    ) -> None:
        self._func = func
        self._owner_candidates = owner_candidates
        self._monitors = monitors or []
        self._validators = validators or []

    async def _prepare_monitors(self, trigger_meta: BulkActionTriggerMeta) -> None:
        for monitor in self._monitors:
            try:
                await monitor.prepare(trigger_meta)
            except Exception as e:
                log.warning("action monitor prepare failed", exc_info=e)

    async def _finalize_monitors(
        self, trigger_meta: BulkActionTriggerMeta, meta: BulkActionResultMeta
    ) -> None:
        process_result = BulkActionProcessResult(meta=meta)
        for monitor in reversed(self._monitors):
            try:
                await monitor.done(trigger_meta, process_result)
            except Exception as e:
                log.warning("action monitor done failed", exc_info=e)

    async def run(self, action: TAction) -> TResult:
        with with_nested_field_action_context(action) as action_id:
            field_id = action.field_id()
            owners = await self._owner_candidates([field_id])
            candidates = list(dict.fromkeys(owners.get(field_id, ())))
            if not candidates:
                raise FieldNotFoundError(
                    "No field row matches the given id",
                    field_type=field_id.field_type(),
                    operation=action.operation_type(),
                )

            started_at = datetime.now(UTC)
            trigger_meta = BulkActionTriggerMeta(
                action_id=action_id,
                started_at=started_at,
                entity_ids=candidates,
                operation_type=action.operation_type(),
                action_name=action.action_name(),
            )

            entity_results: Sequence[BulkEntityResult] = []

            await self._prepare_monitors(trigger_meta)
            try:
                denied: dict[EntityIdentifier, Exception] = {}
                try:
                    for validator in self._validators:
                        denied.update(await validator.validate(trigger_meta))
                except BaseException as e:
                    run_status = ActionRunStatus.of_failure(e, during_validation=True)
                    entity_results = [
                        self._result(field_id, candidate, run_status) for candidate in candidates
                    ]
                    raise
                reached = [candidate for candidate in candidates if candidate not in denied]
                if not reached:
                    refusal = denied[candidates[0]]
                    entity_results = [
                        self._result(
                            field_id,
                            candidates[0],
                            ActionRunStatus.of_failure(refusal, during_validation=True),
                        )
                    ]
                    raise refusal
                try:
                    result = await self._func(action)
                except BaseException as e:
                    run_status = ActionRunStatus.of_failure(e, during_validation=False)
                    entity_results = [self._result(field_id, reached[0], run_status)]
                    raise
                else:
                    entity_results = [self._result(field_id, reached[0], ActionRunStatus.success())]
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
                await self._finalize_monitors(trigger_meta, meta)

    def _result(
        self, field_id: FieldIdentifier, candidate: EntityIdentifier, run_status: ActionRunStatus
    ) -> BulkEntityResult:
        """Name the field row in the description: the entity columns take entity ids only."""
        return BulkEntityResult(
            entity_id=candidate,
            status=run_status.status,
            description=f"{run_status.description} ({field_id})",
            error_code=run_status.error_code,
        )
