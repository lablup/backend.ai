"""Snapshot and resource policy types."""

from dataclasses import dataclass
from typing import Mapping
from uuid import UUID

from ai.backend.common.types import AccessKey, ResourceSlot, SlotName, SlotTypes
from ai.backend.manager.sokovan.scheduler.types import (
    ConcurrencySnapshot,
    KeyPairResourcePolicy,
    PendingSessionSnapshot,
    ResourceOccupancySnapshot,
    ResourcePolicySnapshot,
    SessionDependencySnapshot,
    SystemSnapshot,
    UserResourcePolicy,
)


@dataclass
class ResourcePolicies:
    """Resource policies for scheduling."""

    keypair_policies: dict[AccessKey, KeyPairResourcePolicy]
    user_policies: dict[UUID, UserResourcePolicy]
    group_limits: dict[UUID, ResourceSlot]
    domain_limits: dict[str, ResourceSlot]


@dataclass
class SnapshotData:
    """Snapshot data for system state."""

    resource_occupancy: ResourceOccupancySnapshot
    resource_policies: ResourcePolicies
    session_dependencies: SessionDependencySnapshot

    def to_system_snapshot(
        self, known_slot_types: Mapping[SlotName, SlotTypes], total_capacity: ResourceSlot
    ) -> SystemSnapshot:
        """Convert to SystemSnapshot entity."""
        # Resource policies are already extracted in ResourcePolicies
        resource_policy = ResourcePolicySnapshot(
            keypair_policies=self.resource_policies.keypair_policies,
            user_policies=self.resource_policies.user_policies,
            group_limits=self.resource_policies.group_limits,
            domain_limits=self.resource_policies.domain_limits,
        )

        # Extract concurrency from resource occupancy snapshot
        sessions_by_keypair = {}
        sftp_sessions_by_keypair = {}
        for access_key, occupancy in self.resource_occupancy.by_keypair.items():
            sessions_by_keypair[access_key] = occupancy.session_count
            sftp_sessions_by_keypair[access_key] = occupancy.sftp_session_count

        concurrency = ConcurrencySnapshot(
            sessions_by_keypair=sessions_by_keypair,
            sftp_sessions_by_keypair=sftp_sessions_by_keypair,
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
