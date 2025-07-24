from abc import ABC

from ai.backend.manager.actions.action import BaseAction, BaseActionTriggerMeta


class ActionValidator(ABC):
    async def validate(self, action: BaseAction, meta: BaseActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")
