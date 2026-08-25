from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import ModelDeploymentAccessTokenData
from ai.backend.manager.services.deployment.actions.access_token.base import (
    DeploymentAccessTokenBaseAction,
)


@dataclass
class GetAccessTokenAction(DeploymentAccessTokenBaseAction):
    access_token_id: UUID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_access_token"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetAccessTokenActionResult:
    data: ModelDeploymentAccessTokenData
