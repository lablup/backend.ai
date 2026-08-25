import logging
import uuid
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime

from ai.backend.common.data.entity.types import EntityIdentifier
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
from ai.backend.manager.actions.v2.single_entity.trigger import SingleEntityActionTriggerMeta
from ai.backend.manager.actions.v2.single_entity.validator import SingleEntityActionValidator

__all__ = ("LookupActionProcessor",)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class LookupActionProcessor[TAction: BaseLookupAction, TResult: BaseLookupActionResult]:
    """Validate, run monitors around, then execute a lookup action.

    Authorization comes in two halves, because the key names an entity nobody knows
    until the run produces it: the authentication gate runs first, and the
    post-validators run against the resolved entity. They are the single-entity
    validators, so the permission check a read by id would face is the one a lookup
    faces too.

    A lookup every authenticated caller may resolve is this processor with no
    post-validators.
    """

    _func: Callable[[TAction], Awaitable[TResult]]
    _monitors: Sequence[LookupActionMonitor]
    _validators: Sequence[LookupActionValidator]
    _post_validators: Sequence[SingleEntityActionValidator]

    def __init__(
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        monitors: Sequence[LookupActionMonitor] | None = None,
        validators: Sequence[LookupActionValidator] | None = None,
        post_validators: Sequence[SingleEntityActionValidator] | None = None,
    ) -> None:
        self._func = func
        self._monitors = monitors or []
        self._validators = [AuthenticatedActionValidator(), *(validators or [])]
        self._post_validators = post_validators or []

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

    async def _validate_resolved(
        self,
        action: TAction,
        action_id: uuid.UUID,
        started_at: datetime,
        entity_id: EntityIdentifier,
    ) -> None:
        meta = SingleEntityActionTriggerMeta(
            action_id=action_id,
            started_at=started_at,
            entity=entity_id,
            operation_type=action.operation_type(),
            action_name=action.action_name(),
        )
        for validator in self._post_validators:
            await validator.validate(meta)

    async def run(self, action: TAction) -> TResult:
        started_at = datetime.now(UTC)
        action_id = uuid.uuid4()
        trigger_meta = BaseActionTriggerMeta(action_id=action_id, started_at=started_at)

        run_status = ActionRunStatus.unknown()
        entity_id: EntityIdentifier | None = None

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
                entity_id = result.entity_id()
                try:
                    await self._validate_resolved(action, action_id, started_at, entity_id)
                except BaseException as e:
                    run_status = ActionRunStatus.of_failure(e, during_validation=True)
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
                entity_id=entity_id,
            )
            await self._finalize_monitors(action, meta)
