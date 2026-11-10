from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_serving.types import ErrorInfo
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class ListErrorsAction(ModelServiceAction):
    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "list_errors"


@dataclass
class ListErrorsActionResult:
    error_info: list[ErrorInfo]
    retries: int
