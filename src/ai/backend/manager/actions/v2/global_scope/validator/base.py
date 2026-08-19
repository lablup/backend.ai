from abc import ABC, abstractmethod

from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction

__all__ = ("GlobalActionValidator",)


class GlobalActionValidator(ABC):
    """Validates a global action before execution.

    Independent of the RBAC scope-chain validators: a global action belongs to no
    scope, so there is nothing to resolve against the chain.
    """

    @abstractmethod
    async def validate(self, action: BaseGlobalAction, meta: BaseActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")
