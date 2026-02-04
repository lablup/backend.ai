from abc import abstractmethod
from typing import TypeVar, override

from ai.backend.manager.data.permission.types import OperationType
from ai.backend.manager.repositories.base.types import ActionScope, SearchScope

from .base import BaseAction, BaseActionResult


class BaseScopeAction(BaseAction):
    @override
    def entity_id(self) -> str | None:
        return None

    @abstractmethod
    def scope(self) -> ActionScope:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def permission_operation_type(cls) -> OperationType:
        raise NotImplementedError


class BaseSearchAction(BaseScopeAction):
    @abstractmethod
    def search_scope(self) -> SearchScope:
        raise NotImplementedError


class BaseScopeActionResult(BaseActionResult):
    @override
    def entity_id(self) -> str | None:
        return None

    @abstractmethod
    def scope_type(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def scope_id(self) -> str:
        raise NotImplementedError


TScopeAction = TypeVar("TScopeAction", bound=BaseScopeAction)
TScopeActionResult = TypeVar("TScopeActionResult", bound=BaseScopeActionResult)
