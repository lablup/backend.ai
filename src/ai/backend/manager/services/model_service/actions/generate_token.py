import datetime
import uuid
from dataclasses import dataclass
from typing import Optional, override

from dateutil.relativedelta import relativedelta

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.model_service.actions.base import ModelServiceAction
from ai.backend.manager.services.model_service.types import RequesterCtx


@dataclass
class GenerateTokenAction(ModelServiceAction):
    requester_ctx: RequesterCtx

    service_id: uuid.UUID

    duration: Optional[datetime.timedelta | relativedelta]
    valid_until: Optional[int]
    expires_at: int

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "generate"


@dataclass
class GenerateTokenActionResult(BaseActionResult):
    token: str

    @override
    def entity_id(self) -> Optional[str]:
        return self.token
