from abc import ABC

from ...action.create import BaseCreateAction
from ...types import ActionTriggerMeta, ProcessResult


class CreateActionMonitor(ABC):
    async def prepare(self, action: BaseCreateAction, meta: ActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the prepare method")

    async def done(self, action: BaseCreateAction, result: ProcessResult) -> None:
        raise NotImplementedError("Subclasses must implement the done method")
