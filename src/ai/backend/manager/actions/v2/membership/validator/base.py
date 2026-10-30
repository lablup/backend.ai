from abc import ABC, abstractmethod

from ai.backend.manager.actions.v2.membership.trigger import MembershipActionTriggerMeta

__all__ = ("MembershipActionValidator",)


class MembershipActionValidator(ABC):
    """Validates a membership move before it runs; raises to refuse it."""

    @abstractmethod
    async def validate(self, meta: MembershipActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")
