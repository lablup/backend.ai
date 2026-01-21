from abc import ABC, abstractmethod

from ai.backend.manager.actions.action import BaseAction, BaseActionTriggerMeta


class ActionValidator(ABC):
    @abstractmethod
    async def validate(self, action: BaseAction, meta: BaseActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")
