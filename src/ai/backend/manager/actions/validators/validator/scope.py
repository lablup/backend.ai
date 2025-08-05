from abc import ABC, abstractmethod

from ai.backend.manager.actions.action.scope import BaseScopedAction
from ai.backend.manager.actions.types import ActionTriggerMeta


class ScopedActionValidator(ABC):
    @abstractmethod
    async def validate(self, action: BaseScopedAction, meta: ActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")
