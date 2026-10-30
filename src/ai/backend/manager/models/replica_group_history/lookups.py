"""Lookup spec reaching the deployment a replica-group history row was recorded under."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.replica_group_history import ReplicaGroupHistoryID
from ai.backend.manager.models.replica_group_history.row import ReplicaGroupHistoryRow
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup


@dataclass
class ReplicaGroupHistoryOwnerLookup(FieldOwnerLookup[ReplicaGroupHistoryID, DeploymentID]):
    """The deployment a replica-group history row was recorded under."""

    @override
    def build_query(self, field_ids: Sequence[ReplicaGroupHistoryID]) -> sa.sql.Select[Any]:
        return sa.select(ReplicaGroupHistoryRow.id, ReplicaGroupHistoryRow.deployment_id).where(
            ReplicaGroupHistoryRow.id.in_(field_ids)
        )

    @override
    def to_entity_id(self, value: UUID) -> DeploymentID:
        return DeploymentID(value)
