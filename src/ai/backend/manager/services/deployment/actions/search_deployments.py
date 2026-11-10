"""Deployment search across the whole table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.models.endpoint.row import EndpointRow

__all__ = ("GlobalSearchDeploymentsAction",)


@dataclass(frozen=True)
class GlobalSearchDeploymentsAction(GlobalSearcherOpsAction[EndpointRow, ModelDeploymentData]):
    """Page through every deployment. The SUPERADMIN gate answers for the unscoped read."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DeploymentEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_deployments"
