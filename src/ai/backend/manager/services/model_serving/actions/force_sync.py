import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.model_serving.types import RequesterCtx
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class ForceSyncAction(ModelServiceAction):
    service_id: uuid.UUID
    requester_ctx: RequesterCtx

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
