import logging
import uuid
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from ai.backend.common.exception import PermissionDeniedError
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.action import (
    BaseActionTriggerMeta,
)
from ai.backend.manager.actions.action.bulk import (
    BaseBulkAction,
    BaseBulkActionResult,
)
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.validator.bulk import (
    BulkActionValidator,
    BulkValidationResult,
    DeniedEntity,
)

from .base import ActionRunner

__all__ = (
    "BulkActionProcessor",
    "BulkProcessResult",
    "ValidatorDecision",
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass(frozen=True)
class ValidatorDecision:
    """One validator's per-element verdict observed during bulk processing."""

    validator_name: str
    results: BulkValidationResult


@dataclass(frozen=True)
class BulkProcessResult[TBulkActionResult: BaseBulkActionResult]:
    """Outcome of a ``BulkActionProcessor`` run."""

    result: TBulkActionResult
    validator_decisions: list[ValidatorDecision]


class BulkActionProcessor[
    TBulkAction: BaseBulkAction,
    TBulkActionResult: BaseBulkActionResult,
]:
    _validators: Sequence[BulkActionValidator]

    _runner: ActionRunner[TBulkAction, TBulkActionResult]

    def __init__(
        self,
        func: Callable[[TBulkAction], Awaitable[TBulkActionResult]],
        monitors: Sequence[ActionMonitor] | None = None,
        validators: Sequence[BulkActionValidator] | None = None,
    ) -> None:
        self._runner = ActionRunner(func, monitors)

        self._validators = validators or []

    async def _run(self, action: TBulkAction) -> BulkProcessResult[TBulkActionResult]:
        started_at = datetime.now(UTC)
        action_id = uuid.uuid4()
        action_trigger_meta = BaseActionTriggerMeta(action_id=action_id, started_at=started_at)

        decisions: list[ValidatorDecision] = []
        denied_entities: list[DeniedEntity] = []

        for validator in self._validators:
            validation = await validator.validate(action, action_trigger_meta)
            decisions.append(
                ValidatorDecision(
                    validator_name=validator.name(),
                    results=validation,
                )
            )
            if validation.denied_entities:
                denied_entities.extend(validation.denied_entities)

        if denied_entities:
            err_msg = f"Bulk action denied for {len(denied_entities)} entity(ies): " + ", ".join(
                f"{d.entity_ref.to_str()} ({d.deny_reason})" for d in denied_entities
            )
            raise PermissionDeniedError(err_msg)

        action_result = await self._runner.run(action, action_trigger_meta)
        return BulkProcessResult(result=action_result, validator_decisions=decisions)

    async def wait_for_complete(self, action: TBulkAction) -> BulkProcessResult[TBulkActionResult]:
        return await self._run(action)
