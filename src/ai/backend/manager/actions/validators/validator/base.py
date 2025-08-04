from abc import ABC, abstractmethod

from ai.backend.manager.actions.action.base import BaseAction
from ai.backend.manager.actions.types import ActionTriggerMeta


class ActionValidator(ABC):
    @abstractmethod
    async def validate(self, action: BaseAction, meta: ActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")
