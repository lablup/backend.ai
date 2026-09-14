from abc import ABC

from ai.backend.manager.actions.v2.lookup.base import BaseLookupAction
from ai.backend.manager.actions.v2.lookup.result import LookupActionProcessResult
from ai.backend.manager.actions.v2.trigger import ActionTriggerMeta

__all__ = ("LookupActionMonitor",)


class LookupActionMonitor(ABC):
    """Observes the lifecycle of a lookup action."""

    async def prepare(self, action: BaseLookupAction, meta: ActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the prepare method")

    async def done(self, action: BaseLookupAction, result: LookupActionProcessResult) -> None:
        raise NotImplementedError("Subclasses must implement the done method")
