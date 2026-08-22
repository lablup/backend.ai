from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.access_token import ModelDeploymentAccessTokenCreator
from ai.backend.manager.data.deployment.types import ModelDeploymentAccessTokenData
from ai.backend.manager.services.deployment.actions.access_token.base import (
    DeploymentAccessTokenBaseAction,
)


@dataclass
class CreateAccessTokenAction(DeploymentAccessTokenBaseAction):
    creator: ModelDeploymentAccessTokenCreator

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_access_token"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateAccessTokenActionResult:
    data: ModelDeploymentAccessTokenData
