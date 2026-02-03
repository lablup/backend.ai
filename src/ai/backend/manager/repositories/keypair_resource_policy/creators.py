"""CreatorSpec implementations for keypair resource policy repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.types import DefaultForUnspecified, ResourceSlot
from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class KeyPairResourcePolicyCreatorSpec(CreatorSpec["KeyPairResourcePolicyRow"]):
    """CreatorSpec for keypair resource policy creation."""

    name: str | None
    allowed_vfolder_hosts: dict[str, Any] | None
    default_for_unspecified: DefaultForUnspecified | None
    idle_timeout: int | None
    max_concurrent_sessions: int | None
    max_containers_per_session: int | None
    max_pending_session_count: int | None
    max_pending_session_resource_slots: ResourceSlot | None
    max_quota_scope_size: int | None
    max_vfolder_count: int | None
    max_vfolder_size: int | None
    max_concurrent_sftp_sessions: int | None
    max_session_lifetime: int | None
    total_resource_slots: ResourceSlot | None

    @override
    def build_row(self) -> KeyPairResourcePolicyRow:
        return KeyPairResourcePolicyRow(
            name=self.name,
            default_for_unspecified=self.default_for_unspecified,
            total_resource_slots=self.total_resource_slots,
            max_session_lifetime=self.max_session_lifetime,
            max_concurrent_sessions=self.max_concurrent_sessions,
            max_pending_session_count=self.max_pending_session_count,
            max_pending_session_resource_slots=self.max_pending_session_resource_slots,
            max_concurrent_sftp_sessions=self.max_concurrent_sftp_sessions,
            max_containers_per_session=self.max_containers_per_session,
            idle_timeout=self.idle_timeout,
            allowed_vfolder_hosts=self.allowed_vfolder_hosts,
        )
