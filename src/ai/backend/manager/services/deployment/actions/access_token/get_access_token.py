from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_token import DeploymentTokenID
from ai.backend.manager.actions.v2.field.ops import GetFieldOpsAction
from ai.backend.manager.data.deployment.types import ModelDeploymentAccessTokenData
from ai.backend.manager.models.endpoint.queriers import DeploymentAccessTokenQuerier
from ai.backend.manager.models.endpoint.row import EndpointTokenRow
from ai.backend.manager.services.deployment.actions.lookup_owner import (
    LookupDeploymentAccessTokenOwnerAction,
)


@dataclass
class GetAccessTokenAction(
    GetFieldOpsAction[
        DeploymentTokenID, DeploymentID, EndpointTokenRow, ModelDeploymentAccessTokenData
    ]
):
    """Read one access token, authorized against the deployment it grants access to."""

    access_token_id: DeploymentTokenID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_access_token"

    @override
    def to_owner_lookup_action(self) -> LookupDeploymentAccessTokenOwnerAction:
        return LookupDeploymentAccessTokenOwnerAction(access_token_id=self.access_token_id)

    @override
    def to_querier(self) -> DeploymentAccessTokenQuerier:
        return DeploymentAccessTokenQuerier(access_token_id=self.access_token_id)
