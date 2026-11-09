import logging
import uuid
from collections.abc import Awaitable, Callable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.actions.run_status import ActionRunStatus
from ai.backend.manager.actions.v2.bulk.trigger import BulkActionTriggerMeta
from ai.backend.manager.actions.v2.bulk.validator.base import PartialBulkActionValidator
from ai.backend.manager.actions.v2.lookup.bulk_base import (
    BaseBulkLookupAction,
    BulkLookupKeyResult,
)
from ai.backend.manager.actions.v2.lookup.bulk_monitor.base import BulkLookupActionMonitor
from ai.backend.manager.actions.v2.lookup.bulk_result import (
    BulkLookupActionProcessResult,
    BulkLookupActionResultMeta,
)
from ai.backend.manager.actions.v2.lookup.bulk_trigger import BulkLookupActionTriggerMeta
from ai.backend.manager.actions.v2.lookup.bulk_validator import (
    AuthenticatedBulkLookupActionValidator,
    BulkLookupActionValidator,
)
from ai.backend.manager.actions.v2.lookup.log_context import with_bulk_lookup_action_context
from ai.backend.manager.actions.v2.ops.result import BulkLookupOpsResult
from ai.backend.manager.errors.common import GenericBadRequest

__all__ = ("PartialBulkLookupActionProcessor",)

log = StructuredLogger(logging.getLogger(__spec__.name))


class PartialBulkLookupActionProcessor[TAction: BaseBulkLookupAction]:
    """A bulk lookup gated per key: a key the caller may not reach fails alone.

    A key naming nothing and a key naming an entity the caller may not reach fail with
    the same exception, as a single lookup's do. A superadmin gets the miss as is.
    """

    _func: Callable[[TAction], Awaitable[BulkLookupOpsResult[Any, Any]]]
    _monitors: Sequence[BulkLookupActionMonitor]
    _validators: Sequence[BulkLookupActionValidator]
    _partial_validators: Sequence[PartialBulkActionValidator]

    def __init__(
        self,
        func: Callable[[TAction], Awaitable[BulkLookupOpsResult[Any, Any]]],
        partial_validators: Sequence[PartialBulkActionValidator],
        monitors: Sequence[BulkLookupActionMonitor] | None = None,
        validators: Sequence[BulkLookupActionValidator] | None = None,
    ) -> None:
        self._func = func
        self._monitors = monitors or []
        self._validators = [AuthenticatedBulkLookupActionValidator(), *(validators or [])]
        self._partial_validators = partial_validators

    async def _prepare_monitors(self, trigger_meta: BulkLookupActionTriggerMeta) -> None:
        for monitor in self._monitors:
            try:
                await monitor.prepare(trigger_meta)
            except Exception as e:
                log.warning("action monitor prepare failed", exc_info=e)

    async def _finalize_monitors(
        self, trigger_meta: BulkLookupActionTriggerMeta, meta: BulkLookupActionResultMeta
    ) -> None:
        process_result = BulkLookupActionProcessResult(meta=meta)
        for monitor in reversed(self._monitors):
            try:
                await monitor.done(trigger_meta, process_result)
            except Exception as e:
                log.warning("action monitor done failed", exc_info=e)

    async def run(self, action: TAction) -> BulkLookupOpsResult[Any, Any]:
        with with_bulk_lookup_action_context(action) as action_id:
            started_at = datetime.now(UTC)
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
                        denied = await self._denied(action, action_id, started_at, result)
                    except BaseException as e:
                        run_status = ActionRunStatus.of_failure(e, during_validation=True)
                        key_results = self._same_result_for_every_key(action, run_status)
                        raise
                    else:
                        if not self._caller_is_superadmin():
                            result = result.refused(denied, lambda: self._unresolvable(action))
                        key_results = result.key_results()
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

    async def _denied(
        self,
        action: TAction,
        action_id: uuid.UUID,
        started_at: datetime,
        result: BulkLookupOpsResult[Any, Any],
    ) -> Mapping[EntityIdentifier, Exception]:
        entity_ids = list(dict.fromkeys(result.resolved.values()))
        if not entity_ids:
            return {}
        meta = BulkActionTriggerMeta(
            action_id=action_id,
            started_at=started_at,
            entity_ids=entity_ids,
            operation_type=action.operation_type(),
            action_name=action.action_name(),
        )
        denied: dict[EntityIdentifier, Exception] = {}
        for validator in self._partial_validators:
            denied.update(await validator.validate(meta))
        return denied

    def _caller_is_superadmin(self) -> bool:
        user = current_user()
        return user is not None and user.is_superadmin

    def _unresolvable(self, action: TAction) -> GenericBadRequest:
        """The answer a key gets for either failure; it carries neither the key nor the id."""
        return GenericBadRequest(f"Cannot resolve the given {action.entity_type()} key")

    def _same_result_for_every_key(
        self, action: TAction, run_status: ActionRunStatus
    ) -> Sequence[BulkLookupKeyResult]:
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
