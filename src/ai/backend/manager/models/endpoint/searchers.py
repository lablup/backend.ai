"""List-read specs for deployments and the endpoint sidecar tables."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from ai.backend.manager.data.deployment.types import (
    ModelDeploymentAccessTokenData,
    ModelDeploymentAutoScalingRuleData,
    ModelDeploymentData,
)
from ai.backend.manager.models.endpoint.row import (
    EndpointAutoScalingRuleRow,
    EndpointRow,
    EndpointTokenRow,
)
from ai.backend.manager.models.endpoint.searchable_fields import (
    AutoScalingRuleSearchableFields,
    DeploymentAccessTokenSearchableFields,
    DeploymentSearchableFields,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class DeploymentAccessTokenSearcher(Searcher[EndpointTokenRow, ModelDeploymentAccessTokenData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(EndpointTokenRow)

    @override
    def to_data(self, row: EndpointTokenRow) -> ModelDeploymentAccessTokenData:
        return DeploymentAccessTokenSearchableFields.own.to_data(row)


@dataclass
class AutoScalingRuleSearcher(
    Searcher[EndpointAutoScalingRuleRow, ModelDeploymentAutoScalingRuleData]
):
    """Auto-scaling rules matching the conditions."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(EndpointAutoScalingRuleRow)

    @override
    def to_data(self, row: EndpointAutoScalingRuleRow) -> ModelDeploymentAutoScalingRuleData:
        return AutoScalingRuleSearchableFields.own.to_data(row)


@dataclass
class DeploymentSearcher(Searcher[EndpointRow, ModelDeploymentData]):
    """The deployment rows a page read returns.

    The active revision and the policy live on other rows, so the groups holding them
    are loaded with the page and read onto the projection.
    """

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(EndpointRow).options(
            selectinload(EndpointRow.primary_replica_group_row),
            selectinload(EndpointRow.target_replica_group_row),
            selectinload(EndpointRow.deployment_policy),
        )

    @override
    def to_data(self, row: EndpointRow) -> ModelDeploymentData:
        data = DeploymentSearchableFields.own.to_data(row)
        current_revision_id = row.current_revision_id
        policy = row.deployment_policy.to_data() if row.deployment_policy is not None else None
        return replace(
            data,
            current_revision_id=current_revision_id,
            revision_history_ids=[current_revision_id] if current_revision_id is not None else [],
            policy=policy,
        )
