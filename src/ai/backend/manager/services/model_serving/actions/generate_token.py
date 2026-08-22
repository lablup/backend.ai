from dataclasses import dataclass
from datetime import timedelta
from typing import override

from dateutil.relativedelta import relativedelta

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_serving.types import EndpointTokenData
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class GenerateTokenAction(ModelServiceAction):
    duration: timedelta | relativedelta | None
    valid_until: int | None
    expires_at: int

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "generate_token"


@dataclass
class GenerateTokenActionResult:
    data: EndpointTokenData
