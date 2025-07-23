from abc import ABC

from ai.backend.manager.actions.action.base import BaseAction
from ai.backend.manager.actions.types import ActionTriggerMeta


class ActionValidator(ABC):
    async def validate(self, action: BaseAction, meta: ActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")
