from abc import abstractmethod
from collections.abc import Mapping
from typing import TypeVar, override

from ai.backend.manager.data.permission.types import EntityType, OperationType

from .base import BaseAction, BaseActionResult


class BaseBatchAction(BaseAction):
    @override
    def entity_id(self) -> str | None:
        return None

    @abstractmethod
    def entity_ids(self) -> list[str]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def root_entity_type(cls) -> EntityType | None:
        raise NotImplementedError

    @abstractmethod
    def root_entity_ids(self) -> Mapping[str, str | None]:
        """
        Returns a mapping of entity IDs to their corresponding root entity IDs.
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def permission_operation_type(cls) -> OperationType:
        raise NotImplementedError


class BaseBatchActionResult(BaseActionResult):
    @override
    def entity_id(self) -> str | None:
        return None

    @abstractmethod
    def entity_ids(self) -> list[str]:
        raise NotImplementedError


TBatchAction = TypeVar("TBatchAction", bound=BaseBatchAction)
TBatchActionResult = TypeVar("TBatchActionResult", bound=BaseBatchActionResult)
