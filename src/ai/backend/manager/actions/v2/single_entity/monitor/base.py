from abc import ABC

from ai.backend.manager.actions.v2.single_entity.result import SingleEntityActionProcessResult
from ai.backend.manager.actions.v2.single_entity.trigger import (
    SingleEntityActionTriggerMeta,
)

__all__ = ("SingleEntityActionMonitor",)


class SingleEntityActionMonitor(ABC):
    """Observes the lifecycle of an operation on one entity.

    ``prepare`` runs before the action function; ``done`` runs after it completes (or
    fails), with the outcome carried in :class:`SingleEntityActionProcessResult`. Reads
    the entity from the meta, so the field shape reuses these unchanged.
    """

    async def prepare(self, meta: SingleEntityActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the prepare method")

    async def done(
        self, meta: SingleEntityActionTriggerMeta, result: SingleEntityActionProcessResult
    ) -> None:
        raise NotImplementedError("Subclasses must implement the done method")
