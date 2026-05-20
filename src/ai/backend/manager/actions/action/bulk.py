from abc import abstractmethod
from dataclasses import dataclass
from typing import TypeVar, override

from ai.backend.manager.data.permission.types import RBACElementRef

from .base import BaseAction, BaseActionResult


@dataclass
class BaseBulkAction(BaseAction):
    """Bulk action over a list of ``RBACElementRef`` (may mix element types)."""

    element_refs: list[RBACElementRef]


class BaseBulkActionResult(BaseActionResult):
    @override
    def entity_id(self) -> str | None:
        return None

    @abstractmethod
    def element_refs(self) -> list[RBACElementRef]:
        raise NotImplementedError


TBulkAction = TypeVar("TBulkAction", bound=BaseBulkAction)
TBulkActionResult = TypeVar("TBulkActionResult", bound=BaseBulkActionResult)
