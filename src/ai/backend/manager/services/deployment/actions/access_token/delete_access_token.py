from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.deployment.actions.access_token.base import (
    DeploymentAccessTokenBaseAction,
)


@dataclass
class DeleteAccessTokenAction(DeploymentAccessTokenBaseAction):
    access_token_id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.access_token_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteAccessTokenActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> str | None:
        return None
