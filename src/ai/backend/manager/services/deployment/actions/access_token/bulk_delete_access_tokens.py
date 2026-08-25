from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.deployment.actions.base import DeploymentGlobalAction


@dataclass
class BulkDeleteAccessTokensAction(DeploymentGlobalAction):
    access_token_ids: list[UUID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_delete_access_tokens"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class BulkDeleteAccessTokensActionResult:
    deleted_ids: list[UUID]
