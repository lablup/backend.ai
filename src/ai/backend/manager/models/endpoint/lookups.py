"""Lookup specs reaching a deployment from the rows that live under it."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_token import DeploymentTokenID
from ai.backend.manager.models.endpoint.row import EndpointAutoScalingRuleRow, EndpointTokenRow
from ai.backend.manager.models.specs.lookup import FieldOwnerKeyLookup, FieldOwnerLookup


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
class DeploymentAccessTokenOwnerLookup(FieldOwnerLookup[DeploymentTokenID, DeploymentID]):
    """The deployment an access token grants access to."""

    @override
    def build_query(
        self, field_ids: Sequence[DeploymentTokenID]
    ) -> sa.sql.Select[tuple[DeploymentTokenID, DeploymentID]]:
        return sa.select(EndpointTokenRow.id, EndpointTokenRow.endpoint).where(
            EndpointTokenRow.id.in_(field_ids)
        )

    @override
    def to_entity_id(self, value: UUID) -> DeploymentID:
        return DeploymentID(value)
