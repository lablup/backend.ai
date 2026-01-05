from abc import abstractmethod
from typing import TypeVar, override

from ai.backend.common.data.permission.types import EntityType, OperationType

from .base import BaseAction, BaseActionResult


class BaseSingleEntityAction(BaseAction):
    @override
    def entity_id(self) -> str | None:
        return None

    @abstractmethod
    def target_entity_id(self) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def root_entity_type(cls) -> EntityType | None:
        raise NotImplementedError

    @abstractmethod
    def root_entity_id(self) -> str | None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def permission_operation_type(cls) -> OperationType:
        raise NotImplementedError


class BaseSingleEntityActionResult(BaseActionResult):
    @override
    def entity_id(self) -> str | None:
        return None

    @abstractmethod
    def target_entity_id(self) -> str:
        raise NotImplementedError


TSingleEntityAction = TypeVar("TSingleEntityAction", bound=BaseSingleEntityAction)
TSingleEntityActionResult = TypeVar("TSingleEntityActionResult", bound=BaseSingleEntityActionResult)
