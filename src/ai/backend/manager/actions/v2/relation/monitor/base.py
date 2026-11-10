from abc import ABC

from ai.backend.manager.actions.v2.relation.result import RelationActionProcessResult
from ai.backend.manager.actions.v2.relation.trigger import RelationActionTriggerMeta

__all__ = ("RelationActionMonitor",)


class RelationActionMonitor(ABC):
    """Observes the lifecycle of a link or unlink.

    ``prepare`` runs before the action function; ``done`` runs after it completes (or
    fails), with the outcome carried in :class:`RelationActionProcessResult`.
    """

    async def prepare(self, meta: RelationActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the prepare method")

    async def done(
        self, meta: RelationActionTriggerMeta, result: RelationActionProcessResult
    ) -> None:
        raise NotImplementedError("Subclasses must implement the done method")
