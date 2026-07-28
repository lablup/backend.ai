"""Repository-internal session fetch types."""

from dataclasses import dataclass
from functools import cached_property

from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.session_group import SessionGroupID
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.data.session_group.types import SessionGroupPlacementDirection
from ai.backend.manager.views.sokovan.workload import SessionWorkload


@dataclass
class PendingSessions:
    """Wrapper for pending session workloads with cached owner-key extraction."""

    sessions: list[SessionWorkload]

    @cached_property
    def user_uuids(self) -> set[UserID]:
        """Extract unique user IDs from pending sessions."""
        return {s.meta.owner.user_uuid for s in self.sessions}

    @cached_property
    def project_ids(self) -> set[ProjectID]:
        """Extract unique project IDs from pending sessions."""
        return {s.meta.owner.project_id for s in self.sessions}

    @cached_property
    def domain_ids(self) -> set[DomainID]:
        """Extract unique domain IDs from pending sessions."""
        return {s.meta.owner.domain_id for s in self.sessions}

    @cached_property
    def placement_group_ids(self) -> set[SessionGroupID]:
        """Session groups that actually constrain this pass's placements.

        Groups with a ``none`` direction are left out: they keep the
        membership but do not participate in placement, so their per-agent
        member counts are never read.
        """
        return {
            s.placement.session_group.group_id
            for s in self.sessions
            if s.placement.session_group is not None
            and s.placement.session_group.direction is not SessionGroupPlacementDirection.NONE
        }
