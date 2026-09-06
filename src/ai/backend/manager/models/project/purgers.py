"""Purge specs for the projects table and the rows a project leaves behind."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.data.permission.types import EntityType, ScopeType
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.errors.resource import ProjectHasActiveKernelsError
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.kernel.row import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    KernelRow,
)
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.specs.purger import (
    EntityBatchPurger,
    EntityPurger,
    FieldBatchPurger,
)
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class ProjectKernelPurger(FieldBatchPurger[ProjectID, KernelRow, KernelId]):
    """Clears the kernel rows a project leaves behind, before the project itself goes.

    Kernels stand outside the RBAC graph, so nothing is torn down with them. The owner
    is the project the purge is authorized on, not the session each kernel runs under.
    """

    project_id: ProjectID

    @override
    def build_subquery(self, owner_id: ProjectID) -> sa.sql.Select[Any]:
        return sa.select(KernelRow).where(KernelRow.group_id == owner_id)

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return (
            ConflictCheck(
                condition=lambda: sa.and_(
                    KernelRow.group_id == self.project_id,
                    KernelRow.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES),
                ),
                error=ProjectHasActiveKernelsError(
                    f"error on deleting project {self.project_id} with active kernels"
                ),
            ),
        )

    @override
    def to_data(self, row: KernelRow) -> KernelId:
        return row.id


@dataclass
class ProjectSessionPurger(EntityBatchPurger[SessionRow, SessionID]):
    """Clears the sessions a project leaves behind, each with the RBAC graph it left."""

    project_id: ProjectID

    @override
    def entity_id(self, row: SessionRow) -> EntityIdentifier:
        return SessionID(row.id)

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[SessionRow]]:
        return sa.select(SessionRow).where(SessionRow.group_id == self.project_id)

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: SessionRow) -> SessionID:
        return SessionID(row.id)


@dataclass
class SessionsByIdsPurger(EntityBatchPurger[SessionRow, SessionID]):
    """Clears the named sessions, each with the RBAC graph it left."""

    session_ids: Sequence[SessionId]

    @override
    def entity_id(self, row: SessionRow) -> EntityIdentifier:
        return SessionID(row.id)

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[SessionRow]]:
        return sa.select(SessionRow).where(SessionRow.id.in_(self.session_ids))

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: SessionRow) -> SessionID:
        return SessionID(row.id)


@dataclass
class ProjectEndpointPurger(EntityBatchPurger[EndpointRow, DeploymentID]):
    """Clears the deployments a project leaves behind; their routings go with them
    through the FK cascade."""

    project_id: ProjectID

    @override
    def entity_id(self, row: EndpointRow) -> EntityIdentifier:
        return row.id

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[EndpointRow]]:
        return sa.select(EndpointRow).where(EndpointRow.project == self.project_id)

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: EndpointRow) -> DeploymentID:
        return row.id


@dataclass
class ProjectScopeAssociationPurger(
    FieldBatchPurger[ProjectID, AssociationScopesEntitiesRow, UUID]
):
    """Clears the legacy scope associations a project leaves behind, on both sides: the
    rows enrolling the project under other scopes, and the rows enrolled under the scope
    the project is."""

    @override
    def build_subquery(self, owner_id: ProjectID) -> sa.sql.Select[Any]:
        return sa.select(AssociationScopesEntitiesRow).where(
            sa.or_(
                sa.and_(
                    AssociationScopesEntitiesRow.entity_type == EntityType.PROJECT,
                    AssociationScopesEntitiesRow.entity_id == str(owner_id),
                ),
                sa.and_(
                    AssociationScopesEntitiesRow.scope_type == ScopeType.PROJECT,
                    AssociationScopesEntitiesRow.scope_id == str(owner_id),
                ),
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: AssociationScopesEntitiesRow) -> UUID:
        return row.id


@dataclass
class ProjectPurger(EntityPurger[ProjectRow, ProjectData]):
    """Removes a project along with the scope it was."""

    project_id: ProjectID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.project_id

    @override
    def row_class(self) -> type[ProjectRow]:
        return ProjectRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ProjectRow.id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: ProjectRow) -> ProjectData:
        return row.to_data()
