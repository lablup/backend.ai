from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_serving.types import EndpointData
from ai.backend.manager.models.endpoint.updaters import LegacyEndpointUpdater
from ai.backend.manager.services.model_serving.actions.base import (
    ModelServiceAction,
)


@dataclass
class UpdateEndpointAction(ModelServiceAction):
    updater: LegacyEndpointUpdater

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_endpoint"


@dataclass
class UpdateEndpointActionResult:
    deployment_id: DeploymentID
    success: bool
    data: EndpointData | None
