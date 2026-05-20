from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import override

from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base.types import SearchScope

from .base import BaseAction, BaseActionResult


class BulkActionTarget(ABC):
    @abstractmethod
    def to_rbac_element_ref(self) -> RBACElementRef:
        raise NotImplementedError


class SearchableBulkActionTarget(BulkActionTarget):
    @abstractmethod
    def to_search_scope(self) -> SearchScope:
        raise NotImplementedError


class BaseBulkAction[TTarget: BulkActionTarget](BaseAction):
    """Bulk action over a sequence of :class:`BulkActionTarget`.

    Parametrize the target type to require a richer contract — e.g.
    ``BaseBulkAction[SearchableBulkActionTarget]`` for a scoped search.
    """

    @abstractmethod
    def targets(self) -> Sequence[TTarget]:
        raise NotImplementedError


class BaseBulkActionResult(BaseActionResult):
    @override
    def entity_id(self) -> str | None:
        return None

    @abstractmethod
    def element_refs(self) -> list[RBACElementRef]:
        raise NotImplementedError
