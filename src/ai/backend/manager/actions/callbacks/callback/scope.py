from abc import ABC, abstractmethod

from ai.backend.manager.actions.action.scope import BaseScopedActionResult


class ScopedActionCallback(ABC):
    @abstractmethod
    async def callback(self, result: BaseScopedActionResult) -> None:
        raise NotImplementedError("Subclasses must implement the callback method")
