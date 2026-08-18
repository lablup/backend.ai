import logging
import uuid
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.run_status import ActionRunStatus
from ai.backend.manager.actions.v2.bulk.trigger import BulkActionTriggerMeta
from ai.backend.manager.actions.v2.bulk.validator import BulkActionValidator
from ai.backend.manager.actions.v2.lookup.bulk_base import (
    BaseBulkLookupAction,
    BaseBulkLookupActionResult,
    BulkLookupKeyResult,
)
from ai.backend.manager.actions.v2.lookup.bulk_monitor import BulkLookupActionMonitor
from ai.backend.manager.actions.v2.lookup.bulk_result import (
    BulkLookupActionProcessResult,
    BulkLookupActionResultMeta,
)
from ai.backend.manager.actions.v2.lookup.bulk_trigger import BulkLookupActionTriggerMeta
from ai.backend.manager.actions.v2.lookup.bulk_validator import (
    AuthenticatedBulkLookupActionValidator,
    BulkLookupActionValidator,
)

__all__ = ("BulkLookupActionProcessor",)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class BulkLookupActionProcessor[TAction: BaseBulkLookupAction, TResult: BaseBulkLookupActionResult]:
    """Validate, run monitors around, then execute a bulk lookup.

    Authorization comes in two halves, as the single lookup's does: the authentication
    gate first, then the post-validators against every entity the keys resolved to.
    They are the bulk validators, so the permission a read of those entities would face
    is the one this faces.

    A key that names nothing is one failed key, and the record says so per key; it
    contributes no entity to check.
    """

    _func: Callable[[TAction], Awaitable[TResult]]
    _monitors: Sequence[BulkLookupActionMonitor]
    _validators: Sequence[BulkLookupActionValidator]
    _post_validators: Sequence[BulkActionValidator]

    def __init__(
        self,
        func: Callable[[TAction], Awaitable[TResult]],
        monitors: Sequence[BulkLookupActionMonitor] | None = None,
        validators: Sequence[BulkLookupActionValidator] | None = None,
        post_validators: Sequence[BulkActionValidator] | None = None,
    ) -> None:
        self._func = func
        self._monitors = monitors or []
        self._validators = [AuthenticatedBulkLookupActionValidator(), *(validators or [])]
        self._post_validators = post_validators or []

    async def _prepare_monitors(self, trigger_meta: BulkLookupActionTriggerMeta) -> None:
        for monitor in self._monitors:
            try:
                await monitor.prepare(trigger_meta)
            except Exception as e:
                log.warning("Error in monitor prepare method: {}", e)

    async def _finalize_monitors(
        self, trigger_meta: BulkLookupActionTriggerMeta, meta: BulkLookupActionResultMeta
    ) -> None:
        process_result = BulkLookupActionProcessResult(meta=meta)
        for monitor in reversed(self._monitors):
            try:
                await monitor.done(trigger_meta, process_result)
            except Exception as e:
                log.warning("Error in monitor done method: {}", e)

    async def run(self, action: TAction) -> TResult:
        started_at = datetime.now(UTC)
        action_id = uuid.uuid4()
        trigger_meta = BulkLookupActionTriggerMeta(
            action_id=action_id,
            started_at=started_at,
            entity_type=action.entity_type(),
            operation_type=action.operation_type(),
            action_name=action.action_name(),
        )

        key_results: Sequence[BulkLookupKeyResult] = []

        await self._prepare_monitors(trigger_meta)
        try:
            try:
                for validator in self._validators:
                    await validator.validate(trigger_meta)
            except BaseException as e:
                run_status = ActionRunStatus.of_failure(e, during_validation=True)
                key_results = self._same_result_for_every_key(action, run_status)
                raise
            try:
                result = await self._func(action)
            except BaseException as e:
                run_status = ActionRunStatus.of_failure(e, during_validation=False)
                key_results = self._same_result_for_every_key(action, run_status)
                raise
            else:
                key_results = result.key_results()
                try:
                    await self._validate_resolved(action, action_id, started_at, key_results)
                except BaseException as e:
                    run_status = ActionRunStatus.of_failure(e, during_validation=True)
                    key_results = self._same_result_for_every_key(action, run_status)
                    raise
                else:
                    return result
        finally:
            ended_at = datetime.now(UTC)
            meta = BulkLookupActionResultMeta(
                action_id=action_id,
                key_results=key_results,
                started_at=started_at,
                ended_at=ended_at,
                duration=ended_at - started_at,
            )
            await self._finalize_monitors(trigger_meta, meta)

    async def _validate_resolved(
        self,
        action: TAction,
        action_id: uuid.UUID,
        started_at: datetime,
        key_results: Sequence[BulkLookupKeyResult],
    ) -> None:
        entity_ids = list(
            dict.fromkeys(r.entity_id for r in key_results if r.entity_id is not None)
        )
        if not entity_ids or not self._post_validators:
            return
        meta = BulkActionTriggerMeta(
            action_id=action_id,
            started_at=started_at,
            entity_type=action.entity_type(),
            entity_ids=entity_ids,
            operation_type=action.operation_type(),
            action_name=action.action_name(),
        )
        for validator in self._post_validators:
            await validator.validate(meta)

    def _same_result_for_every_key(
        self, action: TAction, run_status: ActionRunStatus
    ) -> Sequence[BulkLookupKeyResult]:
        """Attribute a whole-run failure to every key the caller named."""
        return [
            BulkLookupKeyResult(
                key=key,
                status=run_status.status,
                description=run_status.description,
                error_code=run_status.error_code,
                entity_id=None,
            )
            for key in action.lookup_keys()
        ]
