import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.data.user.types import UserData
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class DeleteModelServiceAction(ModelServiceAction):
    service_id: uuid.UUID
    user_data: UserData

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete"


@dataclass
class DeleteModelServiceActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
