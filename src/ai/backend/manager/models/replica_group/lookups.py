"""Read specs reaching a deployment from its replica groups."""

from __future__ import annotations

from collections.abc import Sequence
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup


class ReplicaGroupOwnerLookup(FieldOwnerLookup[ReplicaGroupID, DeploymentID]):
    """The deployment a replica group belongs to."""

    @override
    def build_query(
        self, field_ids: Sequence[ReplicaGroupID]
    ) -> sa.sql.Select[tuple[ReplicaGroupID, DeploymentID]]:
        return sa.select(ReplicaGroupRow.id, ReplicaGroupRow.deployment_id).where(
            ReplicaGroupRow.id.in_(field_ids)
        )

    @override
    def to_entity_id(self, value: UUID) -> DeploymentID:
        return DeploymentID(value)
