from abc import abstractmethod
from typing import Optional, TypeVar, override

from ai.backend.manager.data.permission.types import OperationType

from .base import BaseAction, BaseActionResult


class BaseSingleEntityAction(BaseAction):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @abstractmethod
    def target_entity_id(self) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def permission_operation_type(cls) -> OperationType:
        raise NotImplementedError


class BaseSingleEntityActionResult(BaseActionResult):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @abstractmethod
    def target_entity_id(self) -> str:
        raise NotImplementedError


TSingleEntityAction = TypeVar("TSingleEntityAction", bound=BaseSingleEntityAction)
TSingleEntityActionResult = TypeVar("TSingleEntityActionResult", bound=BaseSingleEntityActionResult)
