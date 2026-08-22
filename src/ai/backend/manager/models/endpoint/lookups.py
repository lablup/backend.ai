"""Lookup specs reaching a deployment from the rows that live under it."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.endpoint.row import EndpointAutoScalingRuleRow, EndpointTokenRow
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.specs.lookup import FieldOwnerKeyLookup


@dataclass
class AutoScalingRuleDeploymentLookup(FieldOwnerKeyLookup[DeploymentID]):
    """Reads the deployment an auto-scaling rule belongs to."""

    rule_id: UUID

    @override
    def build_query(self) -> sa.sql.Select[Any]:
        return sa.select(EndpointAutoScalingRuleRow.endpoint).where(
            EndpointAutoScalingRuleRow.id == self.rule_id
        )

    @override
    def to_entity_id(self, value: UUID) -> DeploymentID:
        return DeploymentID(value)


@dataclass
class AccessTokenDeploymentLookup(FieldOwnerKeyLookup[DeploymentID]):
    """Reads the deployment an access token grants access to."""

    access_token_id: UUID

    @override
    def build_query(self) -> sa.sql.Select[Any]:
        return sa.select(EndpointTokenRow.endpoint).where(
            EndpointTokenRow.id == self.access_token_id
        )

    @override
    def to_entity_id(self, value: UUID) -> DeploymentID:
        return DeploymentID(value)


@dataclass
class RouteDeploymentLookup(FieldOwnerKeyLookup[DeploymentID]):
    """Reads the deployment a route belongs to."""

    route_id: UUID

    @override
    def build_query(self) -> sa.sql.Select[Any]:
        return sa.select(RoutingRow.endpoint).where(RoutingRow.id == self.route_id)

    @override
    def to_entity_id(self, value: UUID) -> DeploymentID:
        return DeploymentID(value)


@dataclass
class RevisionDeploymentLookup(FieldOwnerKeyLookup[DeploymentID]):
    """Reads the deployment a revision was taken of."""

    revision_id: UUID

    @override
    def build_query(self) -> sa.sql.Select[Any]:
        return sa.select(DeploymentRevisionRow.endpoint).where(
            DeploymentRevisionRow.id == self.revision_id
        )

    @override
    def to_entity_id(self, value: UUID) -> DeploymentID:
        return DeploymentID(value)
