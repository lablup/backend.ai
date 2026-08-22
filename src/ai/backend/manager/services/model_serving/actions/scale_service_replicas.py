from typing import Self, override

from pydantic import model_validator
from pydantic.dataclasses import dataclass

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.model_serving.actions.base import (
    ModelServiceAction,
)


@dataclass
class ScaleServiceReplicasAction(ModelServiceAction):
    max_session_count_per_model_session: int
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

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scale_service_replicas"


@dataclass
class ScaleServiceReplicasActionResult:
    current_route_count: int
    target_count: int
