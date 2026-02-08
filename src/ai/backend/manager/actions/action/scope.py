from abc import abstractmethod
from typing import TypeVar, override

from ai.backend.common.data.permission.types import ScopeType

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
