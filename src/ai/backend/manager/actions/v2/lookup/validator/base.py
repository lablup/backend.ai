from abc import ABC, abstractmethod

from ai.backend.manager.actions.v2.lookup.base import BaseLookupAction
from ai.backend.manager.actions.v2.trigger import ActionTriggerMeta

__all__ = ("LookupActionValidator",)


class LookupActionValidator(ABC):
    """Validates a lookup action before execution.

    Independent of the RBAC validators: a lookup has no target to resolve against.
    """

    @abstractmethod
    async def validate(self, action: BaseLookupAction, meta: ActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")
