from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_token import DeploymentTokenID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.field.base import BaseSingleFieldAction
from ai.backend.manager.services.deployment.actions.lookup_owner import (
    LookupDeploymentAccessTokenOwnerAction,
)


@dataclass
class DeleteAccessTokenAction(BaseSingleFieldAction[DeploymentTokenID, DeploymentID]):
    """Remove one access token, authorized against the deployment it grants access to."""

    access_token_id: DeploymentTokenID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_access_token"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def to_owner_lookup_action(self) -> LookupDeploymentAccessTokenOwnerAction:
        return LookupDeploymentAccessTokenOwnerAction(access_token_id=self.access_token_id)


@dataclass
class DeleteAccessTokenActionResult:
    success: bool
