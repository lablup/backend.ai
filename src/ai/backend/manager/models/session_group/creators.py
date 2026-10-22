"""Insert specs for session groups."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.session_group.types import (
    SessionGroupData,
    SessionGroupPlacementDirection,
    SessionGroupPlacementEnforcement,
)
from ai.backend.manager.errors.repository import ForeignKeyViolationError, NotNullViolationError
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.session_group.searchable_fields import SessionGroupSearchableFields
from ai.backend.manager.models.specs.creator import EntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class SessionGroupCreator(EntityCreator[SessionGroupRow, SessionGroupData]):
    """A placement group owned by one user within a project.

    Its domain is the project's, resolved by the insert itself. It joins its project and
    its owner, as a session does: admission is the owner's, visibility the project's.
    """

    project_id: ProjectID
    owner_user_id: UserID
    placement_direction: SessionGroupPlacementDirection
    placement_enforcement: SessionGroupPlacementEnforcement

    @override
    def entity_id(self, row: SessionGroupRow) -> SessionGroupID:
        return SessionGroupID(row.id)

    @override
    def created_in(self, row: SessionGroupRow) -> Collection[EntityIdentifier]:
        return (self.project_id, self.owner_user_id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        # A missing project leaves the domain subquery empty before its own FK is checked.
        missing_project = ProjectNotFound(f"Project {self.project_id} not found")
        return (
            IntegrityErrorCheck(violation_type=NotNullViolationError, error=missing_project),
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                error=missing_project,
                constraint_name="fk_session_groups_project_id_groups",
            ),
        )

    @override
    def build_row(self) -> SessionGroupRow:
        return SessionGroupRow(
            domain_id=sa.select(DomainRow.id)
            .join(ProjectRow, ProjectRow.domain_name == DomainRow.name)
            .where(ProjectRow.id == self.project_id)
            .scalar_subquery(),
            project_id=self.project_id,
            owner_user_id=self.owner_user_id,
            placement_direction=self.placement_direction,
            placement_enforcement=self.placement_enforcement,
        )

    @override
    def to_data(self, row: SessionGroupRow) -> SessionGroupData:
        return SessionGroupSearchableFields.own.to_data(row)

    @classmethod
    def for_replica_group(
        cls,
        project_id: ProjectID,
        owner_user_id: UserID,
    ) -> SessionGroupCreator:
        """Build the group a replica group owns: replicas spread across agents
        where possible, without a full agent stopping a rollout."""
        return cls(
            project_id=project_id,
            owner_user_id=owner_user_id,
            placement_direction=SessionGroupPlacementDirection.SPREAD,
            placement_enforcement=SessionGroupPlacementEnforcement.PREFERRED,
        )
