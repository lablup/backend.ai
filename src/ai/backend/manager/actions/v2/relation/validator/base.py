from abc import ABC, abstractmethod

from ai.backend.manager.actions.v2.relation.trigger import RelationActionTriggerMeta

__all__ = ("RelationActionValidator",)


class RelationActionValidator(ABC):
    """Validates a link or unlink before it runs.

    Raises rather than answering per scope: the operation writes one row about both, so
    a scope the caller may not reach leaves nothing to run.
    """

    @abstractmethod
    async def validate(self, meta: RelationActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")
