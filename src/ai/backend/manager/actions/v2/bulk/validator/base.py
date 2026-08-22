from abc import ABC, abstractmethod

from ai.backend.manager.actions.v2.bulk.trigger import BulkActionTriggerMeta

__all__ = ("BulkActionValidator",)


class BulkActionValidator(ABC):
    """Validates a bulk action before execution.

    Bound to the self-contained :class:`BaseBulkAction` (pure ABC), so this
    contract stays independent of the legacy ``BaseAction`` hierarchy.
    """

    @abstractmethod
    async def validate(self, meta: BulkActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")
