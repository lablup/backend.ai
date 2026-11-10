from abc import ABC

from ai.backend.manager.actions.v2.membership.result import MembershipActionProcessResult
from ai.backend.manager.actions.v2.membership.trigger import MembershipActionTriggerMeta

__all__ = ("MembershipActionMonitor",)


class MembershipActionMonitor(ABC):
    """Observes the lifecycle of an entity entering or leaving scopes."""

    async def prepare(self, meta: MembershipActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the prepare method")

    async def done(
        self, meta: MembershipActionTriggerMeta, result: MembershipActionProcessResult
    ) -> None:
        raise NotImplementedError("Subclasses must implement the done method")
