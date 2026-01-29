import logging
import uuid
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime
from typing import Optional

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.action import (
    BaseActionTriggerMeta,
)
from ai.backend.manager.actions.action.scope import (
    BaseScopeAction,
    BaseScopeActionResult,
)
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.validator.scope import ScopeActionValidator

from .base import ActionRunner

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ScopeActionProcessor[
    TScopeAction: BaseScopeAction,
    TScopeActionResult: BaseScopeActionResult,
]:
    _validators: Sequence[ScopeActionValidator]
    _runner: ActionRunner[TScopeAction, TScopeActionResult]

    def __init__(
        self,
        func: Callable[[TScopeAction], Awaitable[TScopeActionResult]],
        monitors: Optional[Sequence[ActionMonitor]] = None,
        validators: Optional[Sequence[ScopeActionValidator]] = None,
    ) -> None:
        self._runner = ActionRunner(func, monitors)
        self._validators = validators or []

    async def _run(self, action: TScopeAction) -> TScopeActionResult:
        started_at = datetime.now(UTC)
        action_id = uuid.uuid4()
        action_trigger_meta = BaseActionTriggerMeta(action_id=action_id, started_at=started_at)
        for validator in self._validators:
            await validator.validate(action, action_trigger_meta)

        return await self._runner.run(action, action_trigger_meta)

    async def wait_for_complete(self, action: TScopeAction) -> TScopeActionResult:
        return await self._run(action)
