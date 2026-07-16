from abc import ABC, abstractmethod

from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.scope.base import BaseScopeAction

__all__ = ("ScopeActionValidator",)


class ScopeActionValidator(ABC):
    """Validates a scope action before execution.

    Bound to the self-contained :class:`BaseScopeAction` (pure ABC), so this
    contract stays independent of the legacy ``BaseAction`` hierarchy.
    """

    @abstractmethod
    async def validate(self, action: BaseScopeAction, meta: BaseActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")
