from abc import ABC, abstractmethod

from ai.backend.manager.actions.v2.single_entity.trigger import (
    SingleEntityActionTriggerMeta,
)

__all__ = ("SingleEntityActionValidator",)


class SingleEntityActionValidator(ABC):
    """Validates an operation on one entity before it runs.

    Reads the entity from the meta rather than from the action, so the field shape —
    whose entity is looked up rather than declared — runs the very same validators.
    """

    @abstractmethod
    async def validate(self, meta: SingleEntityActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")
