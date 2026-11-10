"""Lookup specs for the deployment_policies table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_policy import DeploymentPolicyID
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup


@dataclass
class DeploymentPolicyOwnerLookup(FieldOwnerLookup[DeploymentPolicyID, DeploymentID]):
    """The deployment a policy belongs to."""

    @override
    def build_query(
        self, field_ids: Sequence[DeploymentPolicyID]
    ) -> sa.sql.Select[tuple[DeploymentPolicyID, DeploymentID]]:
        return sa.select(DeploymentPolicyRow.id, DeploymentPolicyRow.endpoint).where(
            DeploymentPolicyRow.id.in_(field_ids)
        )

    @override
    def to_entity_id(self, value: UUID) -> DeploymentID:
        return DeploymentID(value)
