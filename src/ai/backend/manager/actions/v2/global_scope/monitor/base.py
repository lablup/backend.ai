from abc import ABC

from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.global_scope.result import GlobalActionProcessResult

__all__ = ("GlobalActionMonitor",)


class GlobalActionMonitor(ABC):
    """Observes the lifecycle of a global action."""

    async def prepare(self, action: BaseGlobalAction, meta: BaseActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the prepare method")

    async def done(self, action: BaseGlobalAction, result: GlobalActionProcessResult) -> None:
        raise NotImplementedError("Subclasses must implement the done method")
