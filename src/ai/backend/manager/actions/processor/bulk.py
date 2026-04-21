import logging
import uuid
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

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
)

from .base import ActionRunner

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass(frozen=True)
class ValidatorDecision:
    """One validator's per-entity verdict observed during bulk processing.

    Mirrors the ``SubStepResult`` pattern used by the scheduler history so
    callers can trace where in the validator chain each ID was filtered and
    *why*. ``results`` carries the validator's classification unchanged.
    """

    validator_name: str
    results: BulkValidationResult


@dataclass(frozen=True)
class BulkProcessResult[TBulkActionResult: BaseBulkActionResult]:
    """Outcome of a ``BulkActionProcessor`` run.

    ``result`` is what the service function returned for the permitted subset
    of entity IDs. ``validator_decisions`` keeps the per-validator trace in
    iteration order; callers assemble the partial-success response by
    walking it (each decision carries the denied IDs and their reasons).
    """

    result: TBulkActionResult
    validator_decisions: list[ValidatorDecision]


class BulkActionProcessor[
    TBulkAction: BaseBulkAction[Any],
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

    async def _run_validator(
        self,
        validator: BulkActionValidator,
        action: TBulkAction,
        meta: BaseActionTriggerMeta,
    ) -> BulkValidationResult:
        """Invoke one validator and emit its timing/trace log.

        Timing and per-validator logging live here rather than inside each
        validator implementation so the cross-cutting concern has one home.
        """
        started_at = datetime.now(UTC)
        validation = await validator.validate(action, meta)
        duration = (datetime.now(UTC) - started_at).total_seconds()
        log.debug(
            "bulk validator {} saw {} ids, denied {} in {:.3f}s",
            validator.name(),
            len(action.entity_ids),
            len(validation.denied_entities),
            duration,
        )
        return validation

    def _process_action(
        self,
        current_action: TBulkAction,
        validation: BulkValidationResult,
    ) -> TBulkAction:
        """Return a new action narrowed to the IDs this validator permitted.

        Returns the incoming action unchanged when the validator denied
        nothing; otherwise constructs a fresh instance of the same class
        via its ``entity_ids``-only constructor so the original stays
        immutable.
        """
        if not validation.denied_entities:
            return current_action
        allowed_set = set(validation.allowed_entity_ids)
        filtered_ids = [eid for eid in current_action.entity_ids if eid in allowed_set]
        return type(current_action)(entity_ids=filtered_ids)

    async def _run(self, action: TBulkAction) -> BulkProcessResult[TBulkActionResult]:
        started_at = datetime.now(UTC)
        action_id = uuid.uuid4()
        action_trigger_meta = BaseActionTriggerMeta(action_id=action_id, started_at=started_at)

        # Run every validator over the surviving ID set, then invoke the
        # service function once on the final narrowed action — the service
        # must only see IDs that passed every validator.
        current_action: TBulkAction = action
        decisions: list[ValidatorDecision] = []

        for validator in self._validators:
            validation = await self._run_validator(validator, current_action, action_trigger_meta)
            decisions.append(
                ValidatorDecision(
                    validator_name=validator.name(),
                    results=validation,
                )
            )
            current_action = self._process_action(current_action, validation)

        action_result = await self._runner.run(current_action, action_trigger_meta)
        return BulkProcessResult(result=action_result, validator_decisions=decisions)

    async def wait_for_complete(self, action: TBulkAction) -> BulkProcessResult[TBulkActionResult]:
        return await self._run(action)
