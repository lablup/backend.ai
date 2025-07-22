from abc import ABC

from ..action import BaseAction, BaseActionTriggerMeta, ProcessResult


class ActionMonitor(ABC):
    async def prepare(self, action: BaseAction, meta: BaseActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the prepare method")

    async def done(self, action: BaseAction, result: ProcessResult) -> None:
        raise NotImplementedError("Subclasses must implement the done method")
