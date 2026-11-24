"""Searcher spec for the deployment_revisions table."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.manager.data.deployment.types import (
    ModelRevisionData,
    ReplicaGroupLifecycle,
    RevisionServingState,
    RevisionVFolderReference,
    ServingRevisionRef,
)
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision.searchable_fields import (
    ModelRevisionSearchableFields,
)
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ModelRevisionSearcher(Searcher[DeploymentRevisionRow, ModelRevisionData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(DeploymentRevisionRow)

    @override
    def to_data(self, row: DeploymentRevisionRow) -> ModelRevisionData:
        return ModelRevisionSearchableFields.own.to_data(row)


@dataclass
class ServingRevisionsReferencingVFolderSearcher(
    Searcher[DeploymentRevisionRow, ServingRevisionRef]
):
    """The revisions of active deployments in ``state`` that reference the vfolder.

    ``CURRENT`` is what a live replica group serves; ``DEPLOYING`` is what the deployment
    or a live replica group rolls out, and wins when a revision is both.
    """

    vfolder_id: VFolderUUID = field(kw_only=True)
    reference: RevisionVFolderReference = field(kw_only=True)
    state: RevisionServingState = field(kw_only=True)

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return (
            sa.select(DeploymentRevisionRow)
            .join(EndpointRow, EndpointRow.id == DeploymentRevisionRow.endpoint)
            .where(
                EndpointRow.lifecycle_stage.in_(EndpointLifecycle.active_states()),
                self._references_vfolder(),
                self._in_state(),
            )
        )

    def _references_vfolder(self) -> sa.ColumnElement[bool]:
        match self.reference:
            case RevisionVFolderReference.MODEL:
                return DeploymentRevisionRow.model == self.vfolder_id
            case RevisionVFolderReference.EXTRA_MOUNT:
                return DeploymentRevisionRow.extra_mounts.contains([
                    {"vfolder_id": str(self.vfolder_id)}
                ])

    def _in_state(self) -> sa.ColumnElement[bool]:
        deploying = sa.or_(
            EndpointRow.deploying_revision_id.is_not_distinct_from(DeploymentRevisionRow.id),
            self._live_replica_group_points_at(ReplicaGroupRow.target_revision_id),
        )
        match self.state:
            case RevisionServingState.CURRENT:
                return sa.and_(
                    self._live_replica_group_points_at(ReplicaGroupRow.current_revision_id),
                    sa.not_(deploying),
                )
            case RevisionServingState.DEPLOYING:
                return deploying

    @override
    def to_data(self, row: DeploymentRevisionRow) -> ServingRevisionRef:
        return ServingRevisionRef(
            revision_id=row.id,
            revision_number=row.revision_number,
            deployment_id=row.endpoint,
            state=self.state,
        )

    @staticmethod
    def _live_replica_group_points_at(
        revision_column: InstrumentedAttribute[Any],
    ) -> sa.ColumnElement[bool]:
        return sa.exists().where(
            ReplicaGroupRow.deployment_id == DeploymentRevisionRow.endpoint,
            ReplicaGroupRow.lifecycle.not_in(ReplicaGroupLifecycle.terminal_statuses()),
            revision_column == DeploymentRevisionRow.id,
        )
