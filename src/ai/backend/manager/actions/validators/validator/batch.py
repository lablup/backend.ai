from abc import ABC

from ai.backend.manager.actions.action.batch import BaseBatchAction
from ai.backend.manager.actions.types import ActionTriggerMeta


class BatchActionValidator(ABC):
    async def validate(self, action: BaseBatchAction, meta: ActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")
