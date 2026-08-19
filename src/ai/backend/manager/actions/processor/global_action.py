import logging
import uuid
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.action import BaseActionResult, BaseActionTriggerMeta
from ai.backend.manager.actions.action.global_action import BaseGlobalAction
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.validator.global_action import (
    GlobalActionValidator,
    SuperAdminActionValidator,
)

from .base import ActionRunner

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class GlobalActionProcessor[TGlobalAction: BaseGlobalAction, TActionResult: BaseActionResult]:
    """Validate, run monitors around, then execute a super-admin global action.

    A SUPERADMIN gate always runs first (the invariant of the global layer),
    followed by any extra validators, then the action within the monitor
    lifecycle. Global actions belong to no RBAC scope, so this path never
    touches the RBAC scope-chain validators.
    """

    _validators: Sequence[GlobalActionValidator]
    _runner: ActionRunner[TGlobalAction, TActionResult]

    def __init__(
        self,
        func: Callable[[TGlobalAction], Awaitable[TActionResult]],
        monitors: Sequence[ActionMonitor] | None = None,
        validators: Sequence[GlobalActionValidator] | None = None,
    ) -> None:
        self._runner = ActionRunner(func, monitors)
        self._validators = [SuperAdminActionValidator(), *(validators or [])]

    async def _run(self, action: TGlobalAction) -> TActionResult:
        started_at = datetime.now(UTC)
        action_id = uuid.uuid4()
        action_trigger_meta = BaseActionTriggerMeta(action_id=action_id, started_at=started_at)
        for validator in self._validators:
            await validator.validate(action, action_trigger_meta)

        return await self._runner.run(action, action_trigger_meta)

    async def wait_for_complete(self, action: TGlobalAction) -> TActionResult:
        return await self._run(action)
