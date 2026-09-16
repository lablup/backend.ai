from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_token import DeploymentTokenID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.field.bulk_base import BasePartialBulkFieldAction
from ai.backend.manager.services.deployment.actions.lookup_owner import (
    LookupBulkDeploymentAccessTokenOwnerAction,
)


@dataclass
class BulkDeleteAccessTokensAction(BasePartialBulkFieldAction[DeploymentTokenID, DeploymentID]):
    """Remove the named access tokens, each authorized against the deployment it grants access to."""

    access_token_ids: Sequence[DeploymentTokenID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_delete_access_tokens"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def field_ids(self) -> Sequence[DeploymentTokenID]:
        return tuple(self.access_token_ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkDeploymentAccessTokenOwnerAction:
        return LookupBulkDeploymentAccessTokenOwnerAction(access_token_ids=self.access_token_ids)

    @override
    def narrowed_to(self, field_ids: Sequence[DeploymentTokenID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(
            self,
            access_token_ids=[
                token_id for token_id in self.access_token_ids if token_id in allowed
            ],
        )
