from abc import ABC, abstractmethod

from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.action.batch import BaseBatchAction


class BatchActionValidator(ABC):
    @abstractmethod
    async def validate(self, action: BaseBatchAction, meta: BaseActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")
