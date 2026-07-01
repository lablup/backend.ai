from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType


@dataclass(frozen=True)
class QueryMetricAction(BaseAction):
    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass(frozen=True)
class QueryMetricActionResult(BaseActionResult):
    @override
    def entity_id(self) -> str | None:
        return None
