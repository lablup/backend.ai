"""Lookup specs for the routings table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup


@dataclass
class ReplicaOwnerLookup(FieldOwnerLookup[ReplicaID, DeploymentID]):
    """The deployment a replica serves."""

    @override
    def build_query(
        self, field_ids: Sequence[ReplicaID]
    ) -> sa.sql.Select[tuple[ReplicaID, DeploymentID]]:
        return sa.select(RoutingRow.id, RoutingRow.endpoint).where(RoutingRow.id.in_(field_ids))

    @override
    def to_entity_id(self, value: UUID) -> DeploymentID:
        return DeploymentID(value)
