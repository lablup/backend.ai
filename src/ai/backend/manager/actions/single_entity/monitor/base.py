from abc import ABC

from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.actions.single_entity.result import SingleEntityActionProcessResult

__all__ = ("SingleEntityActionMonitor",)


class SingleEntityActionMonitor(ABC):
    """Observes the lifecycle of a single-entity action.

    Bound to the self-contained :class:`BaseSingleEntityAction` (pure ABC). ``prepare``
    runs before the action function; ``done`` runs after it completes (or fails), with
    the outcome carried in :class:`SingleEntityActionProcessResult`.
    """

    async def prepare(self, action: BaseSingleEntityAction, meta: BaseActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the prepare method")

    async def done(
        self, action: BaseSingleEntityAction, result: SingleEntityActionProcessResult
    ) -> None:
        raise NotImplementedError("Subclasses must implement the done method")
