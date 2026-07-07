from abc import abstractmethod
from typing import TypeVar, override

from ai.backend.common.data.permission.types import ScopeType
from ai.backend.manager.data.permission.types import RBACElementRef

from .base import BaseAction, BaseActionResult


class BaseScopeAction(BaseAction):
    @override
    def entity_id(self) -> str | None:
        return None

    @abstractmethod
    def scope_type(self) -> ScopeType:
        raise NotImplementedError

    @abstractmethod
    def scope_id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def target_element(self) -> RBACElementRef:
        """Return the RBAC element reference for the scope this action targets.

        Used by RBAC validators to check whether the current user has the
        required permission on this scope.

        Implementations must construct the RBACElementRef directly from their
        own fields — do not delegate to ``scope_type()`` / ``scope_id()``.
        """
        raise NotImplementedError


class BaseScopeActionResult(BaseActionResult):
    @override
    def entity_id(self) -> str | None:
        return None

    @abstractmethod
    def scope_type(self) -> ScopeType:
        raise NotImplementedError

    @abstractmethod
    def scope_id(self) -> str:
        raise NotImplementedError


TScopeAction = TypeVar("TScopeAction", bound=BaseScopeAction)
TScopeActionResult = TypeVar("TScopeActionResult", bound=BaseScopeActionResult)
