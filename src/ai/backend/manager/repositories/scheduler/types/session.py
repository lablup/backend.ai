"""Repository-internal session fetch types."""

from dataclasses import dataclass
from functools import cached_property

from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.views.sokovan.workload import SessionWorkload


@dataclass
class PendingSessions:
    """Wrapper for pending session workloads with cached owner-key extraction."""

    sessions: list[SessionWorkload]

    @cached_property
    def user_uuids(self) -> set[UserID]:
        """Extract unique user IDs from pending sessions."""
        return {s.user_uuid for s in self.sessions}

    @cached_property
    def project_ids(self) -> set[ProjectID]:
        """Extract unique project IDs from pending sessions."""
        return {s.project_id for s in self.sessions}

    @cached_property
    def domain_ids(self) -> set[DomainID]:
        """Extract unique domain IDs from pending sessions."""
        return {s.domain_id for s in self.sessions}
