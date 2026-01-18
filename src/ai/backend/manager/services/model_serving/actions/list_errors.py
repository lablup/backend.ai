import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.data.user.types import UserData
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.model_serving.types import ErrorInfo
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class ListErrorsAction(ModelServiceAction):
    user_data: UserData
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
