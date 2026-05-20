import uuid
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime
from typing import Any

from ai.backend.common.exception import PermissionDeniedError
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
    DeniedEntity,
)

from .base import ActionRunner

__all__ = ("BulkActionProcessor",)


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

    async def _run(self, action: TBulkAction) -> TBulkActionResult:
        started_at = datetime.now(UTC)
        action_id = uuid.uuid4()
        action_trigger_meta = BaseActionTriggerMeta(action_id=action_id, started_at=started_at)

        denied_entities: list[DeniedEntity] = []
        for validator in self._validators:
            validation = await validator.validate(action, action_trigger_meta)
            if validation.denied_entities:
                denied_entities.extend(validation.denied_entities)

        if denied_entities:
            err_msg = f"Bulk action denied for {len(denied_entities)} entity(ies): " + ", ".join(
                f"{d.entity_ref.to_str()} ({d.deny_reason})" for d in denied_entities
            )
            raise PermissionDeniedError(err_msg)

        return await self._runner.run(action, action_trigger_meta)

    async def wait_for_complete(self, action: TBulkAction) -> TBulkActionResult:
        return await self._run(action)
