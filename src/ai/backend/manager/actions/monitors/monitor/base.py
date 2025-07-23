from abc import ABC

from ...action.base import BaseAction
from ...types import ActionTriggerMeta, ProcessResult


class ActionMonitor(ABC):
    async def prepare(self, action: BaseAction, meta: ActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the prepare method")

    async def done(self, action: BaseAction, result: ProcessResult) -> None:
        raise NotImplementedError("Subclasses must implement the done method")
