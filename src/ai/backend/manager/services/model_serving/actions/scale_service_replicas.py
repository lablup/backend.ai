import uuid
from typing import Optional, Self, override

from pydantic import model_validator
from pydantic.dataclasses import dataclass

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.model_serving.types import RequesterCtx
from ai.backend.manager.services.model_serving.actions.base import (
    ModelServiceAction,
)


@dataclass
class ScaleServiceReplicasAction(ModelServiceAction):
    requester_ctx: RequesterCtx
    max_session_count_per_model_session: int
    service_id: uuid.UUID
    to: int

    @model_validator(mode="after")
    def validate_replica_count(self) -> Self:
        if self.to < 0:
            raise InvalidAPIParameters(
                "Amount of desired session count cannot be a negative number"
            )
        if self.to > self.max_session_count_per_model_session:
            raise InvalidAPIParameters(
                f"Cannot spawn more than {self.max_session_count_per_model_session} sessions for a single service"
            )
        return self

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @classmethod
    def operation_type(cls) -> str:
        return "scale"


@dataclass
class ScaleServiceReplicasActionResult(BaseActionResult):
    current_route_count: int
    target_count: int

    @override
    def entity_id(self) -> Optional[str]:
        return None
