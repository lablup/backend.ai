import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.data.user.types import UserData
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class ForceSyncAction(ModelServiceAction):
    service_id: uuid.UUID
    user_data: UserData

    def entity_id(self) -> Optional[str]:
        return None

    @classmethod
    def operation_type(cls) -> str:
        return "sync"


@dataclass
class ForceSyncActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
