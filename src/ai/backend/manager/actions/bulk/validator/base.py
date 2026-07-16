from abc import ABC, abstractmethod

from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.bulk.base import BaseBulkAction

__all__ = ("BulkActionValidator",)


class BulkActionValidator(ABC):
    """Validates a bulk action before execution.

    Bound to the self-contained :class:`BaseBulkAction` (pure ABC), so this
    contract stays independent of the legacy ``BaseAction`` hierarchy.
    """

    @abstractmethod
    async def validate(self, action: BaseBulkAction, meta: BaseActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")
