from abc import ABC

from ...action.single_entity import BaseSingleEntityAction
from ...types import ActionTriggerMeta, ProcessResult


class SingleEntityActionMonitor(ABC):
    async def prepare(self, action: BaseSingleEntityAction, meta: ActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the prepare method")

    async def done(self, action: BaseSingleEntityAction, result: ProcessResult) -> None:
        raise NotImplementedError("Subclasses must implement the done method")
