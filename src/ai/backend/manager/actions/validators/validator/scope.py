from abc import ABC

from ai.backend.manager.actions.action.scope import BaseScopedAction
from ai.backend.manager.actions.types import ActionTriggerMeta


class ScopedActionValidator(ABC):
    async def validate(self, action: BaseScopedAction, meta: ActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")
