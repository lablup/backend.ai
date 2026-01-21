from abc import ABC, abstractmethod

from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.action.single_entity import BaseSingleEntityAction


class SingleEntityActionValidator(ABC):
    @abstractmethod
    async def validate(self, action: BaseSingleEntityAction, meta: BaseActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")
