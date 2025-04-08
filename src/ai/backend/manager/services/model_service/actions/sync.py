import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.model_service.actions.base import ModelServiceAction
from ai.backend.manager.services.model_service.types import RequesterCtx


@dataclass
class SyncAction(ModelServiceAction):
    service_id: uuid.UUID
    requester_ctx: RequesterCtx

    def entity_id(self) -> Optional[str]:
        return None

    def operation_type(self) -> str:
        return "sync"


@dataclass
class SyncActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
