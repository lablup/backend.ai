"""Snapshot and resource policy types."""

from collections.abc import Mapping
from dataclasses import dataclass

from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import ResourceSlot, SlotName, SlotTypes
from ai.backend.manager.data.sokovan import (
    ConcurrencySnapshot,
    PendingSessionSnapshot,
    ResourceOccupancySnapshot,
    ResourcePolicySnapshot,
    SessionDependencySnapshot,
    SystemSnapshot,
    UserResourcePolicy,
    UserSessionCounts,
)


@dataclass
class ResourcePolicies:
    """Resource policies for scheduling."""

    user_policies: dict[UserID, UserResourcePolicy]
    project_limits: dict[ProjectID, ResourceSlot]
    domain_limits: dict[DomainID, ResourceSlot]


@dataclass
class SnapshotData:
    """Snapshot data for system state."""

    resource_occupancy: ResourceOccupancySnapshot
    resource_policies: ResourcePolicies
    session_dependencies: SessionDependencySnapshot
    user_session_counts: dict[UserID, UserSessionCounts]
    """Global per-user active session counts."""

    def to_system_snapshot(
        self, known_slot_types: Mapping[SlotName, SlotTypes], total_capacity: ResourceSlot
    ) -> SystemSnapshot:
        """Convert to SystemSnapshot entity."""
        # Resource policies are already extracted in ResourcePolicies
        resource_policy = ResourcePolicySnapshot(
            user_policies=self.resource_policies.user_policies,
            project_limits=self.resource_policies.project_limits,
            domain_limits=self.resource_policies.domain_limits,
        )

        # Concurrency counts come from the global per-user session source,
        # not from RG-scoped occupancy.
        sessions_by_user: dict[UserID, int] = {}
        sftp_sessions_by_user: dict[UserID, int] = {}
        for user_id, counts in self.user_session_counts.items():
            sessions_by_user[user_id] = counts.regular
            sftp_sessions_by_user[user_id] = counts.sftp

        concurrency = ConcurrencySnapshot(
            sessions_by_user=sessions_by_user,
            sftp_sessions_by_user=sftp_sessions_by_user,
        )

        # Pending sessions should be fetched from cache or calculated separately if needed
        pending_sessions = PendingSessionSnapshot(by_keypair={})

        return SystemSnapshot(
            total_capacity=total_capacity,
            resource_occupancy=self.resource_occupancy,
            resource_policy=resource_policy,
            concurrency=concurrency,
            pending_sessions=pending_sessions,
            session_dependencies=self.session_dependencies,
            known_slot_types=known_slot_types,
        )
