import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.model_service.actions.base import ModelServiceAction
from ai.backend.manager.services.model_service.types import ErrorInfo, RequesterCtx


@dataclass
class ListErrorsAction(ModelServiceAction):
    requester_ctx: RequesterCtx
    service_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "list"


@dataclass
class ListErrorsActionResult(BaseActionResult):
    error_info: list[ErrorInfo]
    retries: int

    @override
    def entity_id(self) -> Optional[str]:
        return None
