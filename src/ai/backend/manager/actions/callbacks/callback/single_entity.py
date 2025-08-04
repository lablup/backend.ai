from abc import ABC, abstractmethod

from ai.backend.manager.actions.action.single_entity import (
    BaseSingleEntityActionResult,
)


class SingleEntityActionCallback(ABC):
    @abstractmethod
    async def callback(self, result: BaseSingleEntityActionResult) -> None:
        raise NotImplementedError("Subclasses must implement the callback method")
