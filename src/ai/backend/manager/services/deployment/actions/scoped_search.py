"""Deployment search over the scopes deployments are reachable from."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.models.endpoint.row import EndpointRow

__all__ = ("ScopedSearchDeploymentsAction",)


@dataclass(frozen=True)
class ScopedSearchDeploymentsAction(ScopedSearchOpsAction[EndpointRow, ModelDeploymentData]):
    """Page through the deployments the named scopes reach, combined with OR.

    Every scope is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DeploymentEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_deployments"
