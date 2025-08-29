from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.creator import ModelDeploymentAccessTokenCreator
from ai.backend.manager.data.deployment.types_ import (
    ModelDeploymentAccessTokenData,
)
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class CreateAccessTokenAction(DeploymentBaseAction):
    creator: ModelDeploymentAccessTokenCreator

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.creator.model_deployment_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"


@dataclass
class CreateAccessTokenActionResult(BaseActionResult):
    data: ModelDeploymentAccessTokenData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)
