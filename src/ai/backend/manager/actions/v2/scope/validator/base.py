from abc import ABC, abstractmethod

from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.trigger import ActionTriggerMeta

__all__ = ("ScopeActionValidator",)


class ScopeActionValidator(ABC):
    """Validates a scope action before execution.

    Bound to the self-contained :class:`BaseScopeAction` (pure ABC), so this
    contract stays independent of the legacy ``BaseAction`` hierarchy.
    """

    @abstractmethod
    async def validate(self, action: BaseScopeAction, meta: ActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")
