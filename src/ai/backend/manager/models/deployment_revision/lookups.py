"""Lookup specs for the deployment_revisions table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup


@dataclass
class DeploymentRevisionOwnerLookup(FieldOwnerLookup[DeploymentRevisionID, DeploymentID]):
    """The deployment a revision was taken of."""

    @override
    def build_query(
        self, field_ids: Sequence[DeploymentRevisionID]
    ) -> sa.sql.Select[tuple[DeploymentRevisionID, DeploymentID]]:
        return sa.select(DeploymentRevisionRow.id, DeploymentRevisionRow.endpoint).where(
            DeploymentRevisionRow.id.in_(field_ids)
        )

    @override
    def to_entity_id(self, value: UUID) -> DeploymentID:
        return DeploymentID(value)
