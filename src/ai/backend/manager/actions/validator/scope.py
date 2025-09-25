from abc import ABC, abstractmethod

from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.action.scope import BaseScopeAction


class ScopeActionValidator(ABC):
    @abstractmethod
    async def validate(self, action: BaseScopeAction, meta: BaseActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")
