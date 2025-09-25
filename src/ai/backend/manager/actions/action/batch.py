from abc import abstractmethod
from typing import Optional, TypeVar, override

from ai.backend.manager.data.permission.types import OperationType

from .base import BaseAction, BaseActionResult


class BaseBatchAction(BaseAction):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @abstractmethod
    def entity_ids(self) -> list[str]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def permission_operation_type(cls) -> OperationType:
        raise NotImplementedError


class BaseBatchActionResult(BaseActionResult):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @abstractmethod
    def entity_ids(self) -> list[str]:
        raise NotImplementedError


TBatchAction = TypeVar("TBatchAction", bound=BaseBatchAction)
TBatchActionResult = TypeVar("TBatchActionResult", bound=BaseBatchActionResult)
