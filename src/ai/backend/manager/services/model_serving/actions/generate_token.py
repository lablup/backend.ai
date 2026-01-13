import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional, override

from dateutil.relativedelta import relativedelta

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.model_serving.types import EndpointTokenData, RequesterCtx
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class GenerateTokenAction(ModelServiceAction):
    requester_ctx: RequesterCtx

    service_id: uuid.UUID

    duration: Optional[timedelta | relativedelta]
    valid_until: Optional[int]
    expires_at: int

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "generate"


@dataclass
class GenerateTokenActionResult(BaseActionResult):
    data: EndpointTokenData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)
