from abc import ABC

from ...action.scope import BaseScopedAction
from ...types import ActionTriggerMeta, ProcessResult


class ScopedActionMonitor(ABC):
    async def prepare(self, action: BaseScopedAction, meta: ActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the prepare method")

    async def done(self, action: BaseScopedAction, result: ProcessResult) -> None:
        raise NotImplementedError("Subclasses must implement the done method")
