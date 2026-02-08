from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.access_token import ModelDeploymentAccessTokenCreator
from ai.backend.manager.data.deployment.types import ModelDeploymentAccessTokenData
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class CreateAccessTokenAction(DeploymentBaseAction):
    creator: ModelDeploymentAccessTokenCreator

    @override
    def entity_id(self) -> str | None:
        return str(self.creator.model_deployment_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateAccessTokenActionResult(BaseActionResult):
    data: ModelDeploymentAccessTokenData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id)
