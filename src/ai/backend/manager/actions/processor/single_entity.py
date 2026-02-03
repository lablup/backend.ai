import logging
import uuid
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.action import (
    BaseActionTriggerMeta,
)
from ai.backend.manager.actions.action.single_entity import (
    BaseSingleEntityAction,
    BaseSingleEntityActionResult,
)
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.validator.single_entity import SingleEntityActionValidator

from .base import ActionRunner

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class SingleEntityActionProcessor[
    TSingleEntityAction: BaseSingleEntityAction,
    TSingleEntityActionResult: BaseSingleEntityActionResult,
]:
    _validators: Sequence[SingleEntityActionValidator]

    _runner: ActionRunner[TSingleEntityAction, TSingleEntityActionResult]

    def __init__(
        self,
        func: Callable[[TSingleEntityAction], Awaitable[TSingleEntityActionResult]],
        monitors: Sequence[ActionMonitor] | None = None,
        validators: Sequence[SingleEntityActionValidator] | None = None,
    ) -> None:
        self._runner = ActionRunner(func, monitors)

        self._validators = validators or []

    async def _run(self, action: TSingleEntityAction) -> TSingleEntityActionResult:
        started_at = datetime.now(UTC)
        action_id = uuid.uuid4()
        action_trigger_meta = BaseActionTriggerMeta(action_id=action_id, started_at=started_at)
        for validator in self._validators:
            await validator.validate(action, action_trigger_meta)

        return await self._runner.run(action, action_trigger_meta)

    async def wait_for_complete(self, action: TSingleEntityAction) -> TSingleEntityActionResult:
        return await self._run(action)
