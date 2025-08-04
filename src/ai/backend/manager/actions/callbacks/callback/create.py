from abc import ABC, abstractmethod

from ai.backend.manager.actions.action.create import BaseCreateActionResult


class EntityCreateActionCallback(ABC):
    @abstractmethod
    async def callback(self, result: BaseCreateActionResult) -> None:
        raise NotImplementedError("Subclasses must implement the callback method")
