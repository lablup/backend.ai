import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.model_serving.types import ErrorInfo, RequesterCtx
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class ListErrorsAction(ModelServiceAction):
    requester_ctx: RequesterCtx
    service_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list"


@dataclass
class ListErrorsActionResult(BaseActionResult):
    error_info: list[ErrorInfo]
    retries: int

    @override
    def entity_id(self) -> Optional[str]:
        return None
