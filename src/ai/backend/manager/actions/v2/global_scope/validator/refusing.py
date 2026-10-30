from typing import override

from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.global_scope.validator.base import GlobalActionValidator
from ai.backend.manager.actions.v2.trigger import ActionTriggerMeta
from ai.backend.manager.errors.auth import InsufficientPrivilege

__all__ = ("RefusingGlobalActionValidator",)


class RefusingGlobalActionValidator(GlobalActionValidator):
    """Refuses every action, whoever is asking.

    For a registry assembled to read the wiring off rather than to run it. A tool that
    never runs an action still has to state a gate, and this is the one that says so.
    """

    @override
    async def validate(self, action: BaseGlobalAction, meta: ActionTriggerMeta) -> None:
        raise InsufficientPrivilege(
            f"{action.action_name()} was wired without a gate that lets anyone through."
        )
