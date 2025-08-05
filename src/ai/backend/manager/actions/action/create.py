from abc import ABC, abstractmethod
from typing import TypeVar, override

from ai.backend.manager.data.permission.id import ObjectId, ScopeId

from .base import BaseAction


class BaseCreateAction(BaseAction, ABC):
    @classmethod
    @override
    def operation_type(cls) -> str:
        return "create"


class BaseCreateActionResult(ABC):
    @abstractmethod
    def scope_id(self) -> ScopeId:
        raise NotImplementedError

    @abstractmethod
    def entity_id(self) -> ObjectId:
        raise NotImplementedError


TBaseCreateAction = TypeVar("TBaseCreateAction", bound=BaseCreateAction)
TBaseCreateActionResult = TypeVar("TBaseCreateActionResult", bound=BaseCreateActionResult)
