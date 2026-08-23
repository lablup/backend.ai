import logging
import uuid
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, override

from ai.backend.common.data.entity.types import EntityIdentifier, FieldIdentifier
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.run_status import ActionRunStatus
from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.actions.v2.bulk.monitor import BulkActionMonitor
from ai.backend.manager.actions.v2.bulk.result import (
    BulkActionProcessResult,
    BulkActionResultMeta,
    BulkEntityResult,
)
from ai.backend.manager.actions.v2.bulk.trigger import BulkActionTriggerMeta
from ai.backend.manager.actions.v2.bulk.validator import BulkActionValidator
from ai.backend.manager.actions.v2.field.bulk_base import BaseBulkFieldAction
from ai.backend.manager.actions.v2.field.bulk_lookup import (
    BulkFieldOwnerLookupOpsResult,
    LookupBulkFieldOwnerOpsAction,
)
from ai.backend.manager.actions.v2.lookup.bulk_processor import BulkLookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import BulkFieldOpsResult
from ai.backend.manager.errors.repository import EntityNotFoundError

__all__ = (
    "AtomicFieldResultJudge",
    "BulkFieldActionProcessor",
    "FieldResultJudge",
    "PartialFieldResultJudge",
)

type OwnerBulkLookupProcessor = BulkLookupActionProcessor[
    LookupBulkFieldOwnerOpsAction[Any, Any], BulkFieldOwnerLookupOpsResult[Any]
]

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class FieldResultJudge[TResult](ABC):
    """Decides what a run that returned means for each row the caller named."""

    @abstractmethod
    def judge(
        self, result: TResult, owners: Mapping[FieldIdentifier, EntityIdentifier]
    ) -> Sequence[BulkEntityResult]:
        raise NotImplementedError


class PartialFieldResultJudge[TData](FieldResultJudge[BulkFieldOpsResult[TData]]):
    """Some rows may go through while others fail, so the result says which.

    One record per named row, each naming the entity that answered for it. Which row it
    was goes in the description: the entity columns take entity ids only, and rows of
    one owner would otherwise be indistinguishable.
    """

    @override
    def judge(
        self,
        result: BulkFieldOpsResult[TData],
        owners: Mapping[FieldIdentifier, EntityIdentifier],
    ) -> Sequence[BulkEntityResult]:
        success = ActionRunStatus.success()
        results = [
            BulkEntityResult(
                entity_id=owners[field_id],
                status=success.status,
                description=f"{success.description} ({field_id})",
                error_code=success.error_code,
            )
            for field_id in result.successes
            if field_id in owners
        ]
        for field_id, exception in result.errors.items():
            if field_id not in owners:
                continue
            failure = ActionRunStatus.of_failure(exception, during_validation=False)
            results.append(
                BulkEntityResult(
                    entity_id=owners[field_id],
                    status=failure.status,
                    description=f"{failure.description} ({field_id})",
                    error_code=failure.error_code,
                )
            )
        return results


class AtomicFieldResultJudge[TResult](FieldResultJudge[TResult]):
    """The run stood or fell as one, so every owner read shares its outcome.

    The result is never read, so a run whose answer is not per row -- a batch of
    measurements, say -- is judged the same way as one that writes.
    """

    @override
    def judge(
        self, result: TResult, owners: Mapping[FieldIdentifier, EntityIdentifier]
    ) -> Sequence[BulkEntityResult]:
        return [
            BulkEntityResult(
                entity_id=entity_id,
                status=OperationStatus.SUCCESS,
                description="",
                error_code=None,
            )
            for entity_id in dict.fromkeys(owners.values())
        ]


class BulkFieldActionProcessor[TAction: BaseBulkFieldAction[Any, Any], TResult]:
    """Read the owners of every field row named, then run the bulk pipeline against them.

    The owners are read in one go, before anything is checked or recorded, so the
    validators and monitors are the bulk ones, unchanged.

    The answer and the record are kept at different units on purpose: the caller is told
    what became of each row it named, while each audit row names the entity that
    answered for it. A row that is gone is one failed item, not a failed run.
    """

    _func: Callable[[TAction], Awaitable[TResult]]
    _owner_lookup: OwnerBulkLookupProcessor
    _judge: FieldResultJudge[TResult]
    _monitors: Sequence[BulkActionMonitor]
    _validators: Sequence[BulkActionValidator]

    def __init__(
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        owner_lookup: OwnerBulkLookupProcessor,
        judge: FieldResultJudge[TResult],
        monitors: Sequence[BulkActionMonitor] | None = None,
        validators: Sequence[BulkActionValidator] | None = None,
    ) -> None:
        self._func = func
        self._owner_lookup = owner_lookup
        self._judge = judge
        self._monitors = monitors or []
        self._validators = validators or []

    async def _prepare_monitors(self, trigger_meta: BulkActionTriggerMeta) -> None:
        for monitor in self._monitors:
            try:
                await monitor.prepare(trigger_meta)
            except Exception as e:
                log.warning("Error in monitor prepare method: {}", e)

    async def _finalize_monitors(
        self, trigger_meta: BulkActionTriggerMeta, meta: BulkActionResultMeta
    ) -> None:
        process_result = BulkActionProcessResult(meta=meta)
        for monitor in reversed(self._monitors):
            try:
                await monitor.done(trigger_meta, process_result)
            except Exception as e:
                log.warning("Error in monitor done method: {}", e)

    async def run(self, action: TAction) -> TResult:
        lookup_result = await self._owner_lookup.run(action.to_owner_lookup_action())
        owners = lookup_result.owners
        if not owners:
            raise EntityNotFoundError("No field row matches the given ids")

        started_at = datetime.now(UTC)
        action_id = uuid.uuid4()
        distinct = list(dict.fromkeys(owners.values()))
        trigger_meta = BulkActionTriggerMeta(
            action_id=action_id,
            started_at=started_at,
            entity_ids=distinct,
            operation_type=action.operation_type(),
            action_name=action.action_name(),
        )

        entity_results: Sequence[BulkEntityResult] = []

        await self._prepare_monitors(trigger_meta)
        try:
            try:
                for validator in self._validators:
                    await validator.validate(trigger_meta)
            except BaseException as e:
                run_status = ActionRunStatus.of_failure(e, during_validation=True)
                entity_results = [
                    BulkEntityResult(
                        entity_id=entity_id,
                        status=run_status.status,
                        description=run_status.description,
                        error_code=run_status.error_code,
                    )
                    for entity_id in distinct
                ]
                raise
            try:
                result = await self._func(action)
            except BaseException as e:
                run_status = ActionRunStatus.of_failure(e, during_validation=False)
                entity_results = [
                    BulkEntityResult(
                        entity_id=entity_id,
                        status=run_status.status,
                        description=run_status.description,
                        error_code=run_status.error_code,
                    )
                    for entity_id in distinct
                ]
                raise
            else:
                entity_results = self._judge.judge(result, owners)
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
