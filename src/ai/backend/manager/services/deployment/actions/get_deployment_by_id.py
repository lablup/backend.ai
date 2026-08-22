from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.services.deployment.actions.base import (
    DeploymentSingleEntityAction,
)


@dataclass
class GetDeploymentByIdAction(DeploymentSingleEntityAction):
    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_deployment_by_id"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetDeploymentByIdActionResult:
    data: ModelDeploymentData
