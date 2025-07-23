from abc import ABC

from ai.backend.manager.actions.action.single_entity import BaseSingleEntityAction
from ai.backend.manager.actions.types import ActionTriggerMeta


class SingleEntityActionValidator(ABC):
    async def validate(self, action: BaseSingleEntityAction, meta: ActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")
