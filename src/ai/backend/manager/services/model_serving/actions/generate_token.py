import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import override

from dateutil.relativedelta import relativedelta

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_serving.types import EndpointTokenData
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class GenerateTokenAction(ModelServiceAction):
    service_id: uuid.UUID

    duration: timedelta | relativedelta | None
    valid_until: int | None
    expires_at: int

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class GenerateTokenActionResult(BaseActionResult):
    data: EndpointTokenData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id)
