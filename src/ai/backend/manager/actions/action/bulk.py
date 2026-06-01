from abc import abstractmethod
from collections.abc import Sequence
from typing import override

from ai.backend.manager.data.permission.types import RBACElementRef

from .base import BaseAction, BaseActionResult
from .types import ActionTarget


class BaseBulkAction[TTarget: ActionTarget](BaseAction):
    """Bulk action over a sequence of :class:`ActionTarget`.

    Parametrize the target type to require a richer contract — e.g.
    ``BaseBulkAction[SearchableActionTarget]`` for a scoped search.
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
