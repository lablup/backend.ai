from abc import ABC

from ...action.batch import BaseBatchAction
from ...types import ActionTriggerMeta, ProcessResult


class BatchActionMonitor(ABC):
    async def prepare(self, action: BaseBatchAction, meta: ActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the prepare method")

    async def done(self, action: BaseBatchAction, result: ProcessResult) -> None:
        raise NotImplementedError("Subclasses must implement the done method")
