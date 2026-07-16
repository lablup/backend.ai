from abc import ABC

from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.bulk.base import BaseBulkAction
from ai.backend.manager.actions.bulk.result import BulkActionProcessResult

__all__ = ("BulkActionMonitor",)


class BulkActionMonitor(ABC):
    """Observes the lifecycle of a bulk action.

    Bound to the self-contained :class:`BaseBulkAction` (pure ABC). ``prepare``
    runs before the action function; ``done`` runs after it completes (or fails), with
    the outcome carried in :class:`BulkActionProcessResult`.
    """

    async def prepare(self, action: BaseBulkAction, meta: BaseActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the prepare method")

    async def done(self, action: BaseBulkAction, result: BulkActionProcessResult) -> None:
        raise NotImplementedError("Subclasses must implement the done method")
