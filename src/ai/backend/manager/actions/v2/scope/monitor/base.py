from abc import ABC

from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import ScopeActionProcessResult
from ai.backend.manager.actions.v2.trigger import ActionTriggerMeta

__all__ = ("ScopeActionMonitor",)


class ScopeActionMonitor(ABC):
    """Observes the lifecycle of a scope action.

    Bound to the self-contained :class:`BaseScopeAction` (pure ABC). ``prepare``
    runs before the action function; ``done`` runs after it completes (or fails), with
    the outcome carried in :class:`ScopeActionProcessResult`.
    """

    async def prepare(self, action: BaseScopeAction, meta: ActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the prepare method")

    async def done(self, action: BaseScopeAction, result: ScopeActionProcessResult) -> None:
        raise NotImplementedError("Subclasses must implement the done method")
