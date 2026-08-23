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
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.specs.creator import EntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class SessionGroupCreator(EntityCreator[SessionGroupRow, SessionGroupData]):
    """A placement group owned by one user within a domain and project.

    The ownership scope is taken as the domain *name* because the creating
    entities (an endpoint, a replica group) carry the name rather than the id;
    the id is resolved by the insert itself.

    It joins its project and its owner, as a session does: admission is the
    owner's, visibility the project's.
    """

    domain_name: str
    project_id: ProjectID
    owner_user_id: UserID
    placement_direction: SessionGroupPlacementDirection
    placement_enforcement: SessionGroupPlacementEnforcement

    @override
    def entity_id(self, row: SessionGroupRow) -> SessionGroupID:
        return SessionGroupID(row.id)

    @override
    def member_of(self, row: SessionGroupRow) -> Collection[EntityIdentifier]:
        return (self.project_id, self.owner_user_id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> SessionGroupRow:
        return SessionGroupRow(
            domain_id=sa.select(DomainRow.id)
            .where(DomainRow.name == self.domain_name)
            .scalar_subquery(),
            project_id=self.project_id,
            owner_user_id=self.owner_user_id,
            placement_direction=self.placement_direction,
            placement_enforcement=self.placement_enforcement,
        )

    @override
    def to_data(self, row: SessionGroupRow) -> SessionGroupData:
        return row.to_data()

    @classmethod
    def for_replica_group(
        cls,
        domain_name: str,
        project_id: ProjectID,
        owner_user_id: UserID,
    ) -> SessionGroupCreator:
        """Build the group a replica group owns: replicas spread across agents
        where possible, without a full agent stopping a rollout."""
        return cls(
            domain_name=domain_name,
            project_id=project_id,
            owner_user_id=owner_user_id,
            placement_direction=SessionGroupPlacementDirection.SPREAD,
            placement_enforcement=SessionGroupPlacementEnforcement.PREFERRED,
        )
