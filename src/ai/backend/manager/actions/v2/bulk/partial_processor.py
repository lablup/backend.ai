import logging
import uuid
from collections.abc import Awaitable, Callable, Mapping, Sequence
from datetime import UTC, datetime
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.exception import UnreachableError
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.run_status import ActionRunStatus
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BasePartialBulkAction
from ai.backend.manager.actions.v2.bulk.monitor import BulkActionMonitor
from ai.backend.manager.actions.v2.bulk.result import (
    BulkActionProcessResult,
    BulkActionResultMeta,
    BulkEntityResult,
    PartialBulkEntityResult,
    PartialBulkResult,
)
from ai.backend.manager.actions.v2.bulk.trigger import BulkActionTriggerMeta
from ai.backend.manager.actions.v2.bulk.validator import (
    AtomicBulkActionValidator,
    AuthenticatedAtomicBulkActionValidator,
    PartialBulkActionValidator,
)
from ai.backend.manager.errors.common import ServerMisconfiguredError

__all__ = (
    "PartialBulkActionProcessor",
    "PublicPartialBulkActionProcessor",
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

type PartialBulkFunc[TAction, TData] = Callable[[TAction], Awaitable[PartialBulkResult[TData]]]


class PartialBulkActionProcessor[TAction: BasePartialBulkAction, TData]:
    """Run a bulk action over the entities the caller may reach, and fail the rest.

    Unlike :class:`BulkActionProcessor`, a denied entity does not sink the run: the
    validators say which entities are denied, the operation runs against the others,
    and both kinds of failure reach the caller in one result. The atomic validators
    beside them still refuse the run as a whole — the public path's gate is one.

    The operation is run against the action narrowed to those others, so what the
    caller was denied is never queried and the operation keeps the one-argument
    signature every other generic service has.

    Completing the answer is this class's job, not the operation's: it holds the ids
    the caller named, so it is the only place that can put the denials back beside
    what was read and hand the whole thing back in the order it was asked for.
    """

    _func: PartialBulkFunc[TAction, TData]
    _monitors: Sequence[BulkActionMonitor]
    _atomic_validators: Sequence[AtomicBulkActionValidator]
    _partial_validators: Sequence[PartialBulkActionValidator]

    def __init__(
        self,
        func: PartialBulkFunc[TAction, TData],
        monitors: Sequence[BulkActionMonitor] | None = None,
        atomic_validators: Sequence[AtomicBulkActionValidator] | None = None,
        partial_validators: Sequence[PartialBulkActionValidator] | None = None,
    ) -> None:
        self._func = func
        self._monitors = monitors or []
        self._atomic_validators = atomic_validators or []
        self._partial_validators = partial_validators or []

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

    async def run(self, action: TAction) -> PartialBulkResult[TData]:
        started_at = datetime.now(UTC)
        action_id = uuid.uuid4()
        trigger_meta = BulkActionTriggerMeta(
            action_id=action_id,
            started_at=started_at,
            entity_ids=action.entity_ids(),
            operation_type=action.operation_type(),
            action_name=action.action_name(),
        )

        entity_results: Sequence[BulkEntityResult] = []

        # Validation runs inside the monitor lifecycle so a rejected action is
        # recorded too; monitors that only wrapped execution missed every denial.
        await self._prepare_monitors(trigger_meta)
        try:
            denied: dict[EntityIdentifier, Exception] = {}
            try:
                for atomic_validator in self._atomic_validators:
                    await atomic_validator.validate(trigger_meta)
                for partial_validator in self._partial_validators:
                    denied.update(await partial_validator.validate(trigger_meta))
            except BaseException as e:
                run_status = ActionRunStatus.of_failure(e, during_validation=True)
                entity_results = self._same_result_for_every_entity(trigger_meta, run_status)
                raise
            allowed = [
                entity_id for entity_id in trigger_meta.entity_ids if entity_id not in denied
            ]
            try:
                result = await self._func(action.narrowed_to(allowed))
            except BaseException as e:
                run_status = ActionRunStatus.of_failure(e, during_validation=False)
                entity_results = self._same_result_for_every_entity(trigger_meta, run_status)
                raise
            else:
                answer = self._complete(trigger_meta, result, denied)
                entity_results = [self._recorded(item) for item in answer.items]
                return answer
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

    def _complete(
        self,
        trigger_meta: BulkActionTriggerMeta,
        result: PartialBulkResult[TData],
        denied: Mapping[EntityIdentifier, Exception],
    ) -> PartialBulkResult[TData]:
        """Put the denials back beside what was read, in the order the caller asked.

        An id the operation did not answer for and was not denied is a broken
        contract, so it is reported as one rather than dropped.
        """
        answered = {item.entity_id: item for item in result.items}
        items = []
        for entity_id in trigger_meta.entity_ids:
            denial = denied.get(entity_id)
            if denial is not None:
                items.append(PartialBulkEntityResult[TData].denied(entity_id, denial))
                continue
            item = answered.get(entity_id)
            if item is None:
                item = PartialBulkEntityResult[TData].failed(
                    entity_id,
                    UnreachableError(f"{trigger_meta.action_name} did not answer for {entity_id}"),
                )
            items.append(item)
        return PartialBulkResult(items=items)

    def _recorded(self, item: PartialBulkEntityResult[TData]) -> BulkEntityResult:
        """Turn one answer into the audit row's columns.

        The one place the classification runs: a denial is DENIED because it came
        from a validator, and every other failure is an ordinary error.
        """
        if item.error is None:
            run_status = ActionRunStatus.success()
        else:
            run_status = ActionRunStatus.of_failure(
                item.error, during_validation=item.during_validation
            )
        return BulkEntityResult(
            entity_id=item.entity_id,
            status=run_status.status,
            description=item.description or run_status.description,
            error_code=run_status.error_code,
        )

    def _same_result_for_every_entity(
        self, trigger_meta: BulkActionTriggerMeta, run_status: ActionRunStatus
    ) -> Sequence[BulkEntityResult]:
        """Attribute a whole-run failure to every entity the caller named."""
        return [
            BulkEntityResult(
                entity_id=entity_id,
                status=run_status.status,
                description=run_status.description,
                error_code=run_status.error_code,
            )
            for entity_id in trigger_meta.entity_ids
        ]


class PublicPartialBulkActionProcessor[TAction: BasePartialBulkAction, TData](
    PartialBulkActionProcessor[TAction, TData]
):
    """Validate authentication only, then read every entity the caller named.

    The shape stays bulk, so each entity still gets its own audit row; only the RBAC
    validators are left off, which leaves nothing to deny. The constructor rejects
    writes.
    """

    @override
    def __init__(
        self,
        action_cls: type[TAction],
        func: PartialBulkFunc[TAction, TData],
        monitors: Sequence[BulkActionMonitor] | None = None,
        atomic_validators: Sequence[AtomicBulkActionValidator] | None = None,
    ) -> None:
        operation_type = action_cls.operation_type()
        if operation_type not in ActionOperationType.read_operations():
            raise ServerMisconfiguredError(
                f"{action_cls.__name__} declares operation_type()={operation_type}, "
                "but the public path only accepts read actions."
            )
        super().__init__(
            func,
            monitors=monitors,
            atomic_validators=[
                AuthenticatedAtomicBulkActionValidator(),
                *(atomic_validators or []),
            ],
        )
