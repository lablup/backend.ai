from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.manager.actions.v2.field.ops import GetFieldOpsAction
from ai.backend.manager.data.deployment.types import ModelRevisionData
from ai.backend.manager.models.deployment_revision.queriers import ModelRevisionQuerier
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.services.deployment.actions.lookup_owner import (
    LookupDeploymentRevisionOwnerAction,
)


@dataclass
class GetRevisionByIdAction(
    GetFieldOpsAction[DeploymentRevisionID, DeploymentID, DeploymentRevisionRow, ModelRevisionData]
):
    """Read one revision, authorized against the deployment it was taken of."""

    revision_id: DeploymentRevisionID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_revision_by_id"

    @override
    def to_owner_lookup_action(self) -> LookupDeploymentRevisionOwnerAction:
        return LookupDeploymentRevisionOwnerAction(revision_id=self.revision_id)

    @override
    def to_querier(self) -> ModelRevisionQuerier:
        return ModelRevisionQuerier(revision_id=self.revision_id)
