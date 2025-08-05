from abc import ABC, abstractmethod

from ai.backend.manager.actions.action.create import BaseCreateAction
from ai.backend.manager.actions.types import ActionTriggerMeta


class CreateActionValidator(ABC):
    @abstractmethod
    async def validate(self, action: BaseCreateAction, meta: ActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")
