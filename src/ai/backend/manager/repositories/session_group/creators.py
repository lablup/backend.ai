"""CreatorSpecs for session group inserts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.data.session_group.types import (
    SessionGroupPlacementDirection,
    SessionGroupPlacementEnforcement,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.repositories.base.creator import CreatorSpec


@dataclass
class SessionGroupCreatorSpec(CreatorSpec[SessionGroupRow]):
    """A placement group owned by one user within a domain and project.

    The ownership scope is taken as the domain *name* because the creating
    entities (an endpoint, a replica group) carry the name rather than the id;
    the id is resolved by the insert itself.
    """

    domain_name: str
    project_id: ProjectID
    owner_user_id: UserID
    placement_direction: SessionGroupPlacementDirection
    placement_enforcement: SessionGroupPlacementEnforcement

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

    @classmethod
    def for_replica_group(
        cls,
        domain_name: str,
        project_id: ProjectID,
        owner_user_id: UserID,
    ) -> SessionGroupCreatorSpec:
        """Build the group a replica group owns: replicas spread across agents
        where possible, without a full agent stopping a rollout."""
        return cls(
            domain_name=domain_name,
            project_id=project_id,
            owner_user_id=owner_user_id,
            placement_direction=SessionGroupPlacementDirection.SPREAD,
            placement_enforcement=SessionGroupPlacementEnforcement.PREFERRED,
        )
