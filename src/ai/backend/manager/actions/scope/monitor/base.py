from abc import ABC

from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.scope.base import BaseScopeAction
from ai.backend.manager.actions.scope.result import ScopeActionProcessResult

__all__ = ("ScopeActionMonitor",)


class ScopeActionMonitor(ABC):
    """Observes the lifecycle of a scope action.

    Bound to the self-contained :class:`BaseScopeAction` (pure ABC). ``prepare``
    runs before the action function; ``done`` runs after it completes (or fails), with
    the outcome carried in :class:`ScopeActionProcessResult`.
    """

    async def prepare(self, action: BaseScopeAction, meta: BaseActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the prepare method")

    async def done(self, action: BaseScopeAction, result: ScopeActionProcessResult) -> None:
        raise NotImplementedError("Subclasses must implement the done method")
