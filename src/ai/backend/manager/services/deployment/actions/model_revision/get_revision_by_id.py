from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import (
    ModelRevisionData,
)
from ai.backend.manager.services.deployment.actions.model_revision.base import (
    ModelRevisionBaseAction,
)


@dataclass
class GetRevisionByIdAction(ModelRevisionBaseAction):
    revision_id: DeploymentRevisionID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_revision_by_id"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetRevisionByIdActionResult:
    data: ModelRevisionData
