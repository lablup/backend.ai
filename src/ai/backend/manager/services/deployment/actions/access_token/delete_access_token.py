from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.deployment.actions.access_token.base import (
    DeploymentAccessTokenBaseAction,
)


@dataclass
class DeleteAccessTokenAction(DeploymentAccessTokenBaseAction):
    access_token_id: UUID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_access_token"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteAccessTokenActionResult:
    success: bool
