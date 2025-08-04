from abc import ABC, abstractmethod

from ai.backend.manager.actions.action.batch import BaseBatchActionResult


class BatchActionCallback(ABC):
    @abstractmethod
    async def callback(self, result: BaseBatchActionResult) -> None:
        raise NotImplementedError("Subclasses must implement the callback method")
