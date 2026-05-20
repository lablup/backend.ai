from abc import abstractmethod
from typing import TypeVar, override

from ai.backend.manager.data.permission.types import RBACElementRef

from .base import BaseAction, BaseActionResult


class BaseBulkAction(BaseAction):
    """Bulk action over a list of ``RBACElementRef`` (may mix element types).

    For example, a scoped audit-log search may pass refs of different
    types — ``[(PROJECT, p1), (DOMAIN, default)]``.
    """

    @abstractmethod
    def element_refs(self) -> list[RBACElementRef]:
        raise NotImplementedError


class BaseBulkActionResult(BaseActionResult):
    @override
    def entity_id(self) -> str | None:
        return None

    @abstractmethod
    def element_refs(self) -> list[RBACElementRef]:
        raise NotImplementedError


TBulkAction = TypeVar("TBulkAction", bound=BaseBulkAction)
TBulkActionResult = TypeVar("TBulkActionResult", bound=BaseBulkActionResult)
