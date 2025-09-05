import logging
import uuid
from datetime import datetime
from typing import Awaitable, Callable, Generic, Optional

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.validator.single_entity import SingleEntityActionValidator

from ..action import (
    BaseActionTriggerMeta,
)
from ..action.single_entity import TSingleEntityAction, TSingleEntityActionResult
from ..monitors.monitor import ActionMonitor
from .base import ActionRunner

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class SingleEntityActionProcessor(Generic[TSingleEntityAction, TSingleEntityActionResult]):
    _validators: list[SingleEntityActionValidator]

    _runner: ActionRunner[TSingleEntityAction, TSingleEntityActionResult]

    def __init__(
        self,
        func: Callable[[TSingleEntityAction], Awaitable[TSingleEntityActionResult]],
        monitors: Optional[list[ActionMonitor]] = None,
        validators: Optional[list[SingleEntityActionValidator]] = None,
    ) -> None:
        self._runner = ActionRunner(func, monitors)

        self._validators = validators or []

    async def _run(self, action: TSingleEntityAction) -> TSingleEntityActionResult:
        started_at = datetime.now()
        action_id = uuid.uuid4()
        action_trigger_meta = BaseActionTriggerMeta(action_id=action_id, started_at=started_at)
        for validator in self._validators:
            await validator.validate(action, action_trigger_meta)

        return await self._runner.run(action, action_trigger_meta)

    async def wait_for_complete(self, action: TSingleEntityAction) -> TSingleEntityActionResult:
        return await self._run(action)
