from abc import ABC, abstractmethod

from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.single_entity.base import BaseSingleEntityAction

__all__ = ("SingleEntityActionValidator",)


class SingleEntityActionValidator(ABC):
    """Validates a single-entity action before execution.

    Bound to the self-contained :class:`BaseSingleEntityAction` (pure ABC), so this
    contract stays independent of the legacy ``BaseAction`` hierarchy.
    """

    @abstractmethod
    async def validate(self, action: BaseSingleEntityAction, meta: BaseActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")
