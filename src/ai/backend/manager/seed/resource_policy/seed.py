from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import override

from pydantic import Field

from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyUUID,
    ProjectResourcePolicyUUID,
    UserResourcePolicyUUID,
)
from ai.backend.common.types import DefaultForUnspecified, ResourceSlot, VFolderHostPermission
from ai.backend.manager.models.resource_policy.upserters import (
    KeyPairResourcePolicyUpserter,
    ProjectResourcePolicyUpserter,
    UserResourcePolicyUpserter,
)
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class KeyPairResourcePolicySeed(SeedItem):
    """One ``keypair_resource_policies`` row."""

    uuid: KeyPairResourcePolicyUUID
    name: str = Field(min_length=1, max_length=256)
    total_resource_slots: dict[str, Decimal]
    max_concurrent_sessions: int
    max_containers_per_session: int
    idle_timeout: int
    is_default: bool = False
    default_for_unspecified: DefaultForUnspecified = DefaultForUnspecified.LIMITED
    max_session_lifetime: int = 0
    max_pending_session_count: int | None = None
    max_pending_session_resource_slots: dict[str, Decimal] | None = None
    max_priority: int | None = None
    max_concurrent_sftp_sessions: int = 1
    allowed_vfolder_hosts: dict[str, list[VFolderHostPermission]] = {}

    @override
    def key(self) -> str:
        return str(self.uuid)

    @override
    def write(self) -> SeedWrite:
        pending_slots = self.max_pending_session_resource_slots
        return SeedWrite(
            upserter=KeyPairResourcePolicyUpserter(
                uuid=self.uuid,
                name=self.name,
                is_default=self.is_default,
                default_for_unspecified=self.default_for_unspecified,
                total_resource_slots=ResourceSlot(self.total_resource_slots),
                max_session_lifetime=self.max_session_lifetime,
                max_concurrent_sessions=self.max_concurrent_sessions,
                max_pending_session_count=self.max_pending_session_count,
                max_pending_session_resource_slots=(
                    ResourceSlot(pending_slots) if pending_slots is not None else None
                ),
                max_priority=self.max_priority,
                max_concurrent_sftp_sessions=self.max_concurrent_sftp_sessions,
                max_containers_per_session=self.max_containers_per_session,
                idle_timeout=self.idle_timeout,
                allowed_vfolder_hosts={
                    host: sorted(set(permissions))
                    for host, permissions in self.allowed_vfolder_hosts.items()
                },
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[KeyPairResourcePolicySeed]]) -> list[SeedRejection]:
        return []


class UserResourcePolicySeed(SeedItem):
    """One ``user_resource_policies`` row."""

    uuid: UserResourcePolicyUUID
    name: str = Field(min_length=1, max_length=256)
    max_vfolder_count: int
    max_quota_scope_size: int
    max_session_count_per_model_session: int
    max_customized_image_count: int = 3
    max_concurrent_logins: int | None = None

    @override
    def key(self) -> str:
        return str(self.uuid)

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=UserResourcePolicyUpserter(
                uuid=self.uuid,
                name=self.name,
                max_vfolder_count=self.max_vfolder_count,
                max_quota_scope_size=self.max_quota_scope_size,
                max_session_count_per_model_session=self.max_session_count_per_model_session,
                max_customized_image_count=self.max_customized_image_count,
                max_concurrent_logins=self.max_concurrent_logins,
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[UserResourcePolicySeed]]) -> list[SeedRejection]:
        return []


class ProjectResourcePolicySeed(SeedItem):
    """One ``project_resource_policies`` row."""

    uuid: ProjectResourcePolicyUUID
    name: str = Field(min_length=1, max_length=256)
    max_vfolder_count: int
    max_quota_scope_size: int
    max_network_count: int

    @override
    def key(self) -> str:
        return str(self.uuid)

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=ProjectResourcePolicyUpserter(
                uuid=self.uuid,
                name=self.name,
                max_vfolder_count=self.max_vfolder_count,
                max_quota_scope_size=self.max_quota_scope_size,
                max_network_count=self.max_network_count,
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[ProjectResourcePolicySeed]]) -> list[SeedRejection]:
        return []
