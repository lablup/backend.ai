"""CreatorSpec implementations for keypair resource policy repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from typing_extensions import override

from ai.backend.common.types import DefaultForUnspecified, ResourceSlot
from ai.backend.manager.repositories.base import CreatorSpec

if TYPE_CHECKING:
    from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow


@dataclass
class KeyPairResourcePolicyCreatorSpec(CreatorSpec["KeyPairResourcePolicyRow"]):
    """CreatorSpec for keypair resource policy creation."""

    name: Optional[str]
    allowed_vfolder_hosts: Optional[dict[str, Any]]
    default_for_unspecified: Optional[DefaultForUnspecified]
    idle_timeout: Optional[int]
    max_concurrent_sessions: Optional[int]
    max_containers_per_session: Optional[int]
    max_pending_session_count: Optional[int]
    max_pending_session_resource_slots: Optional[ResourceSlot]
    max_quota_scope_size: Optional[int]
    max_vfolder_count: Optional[int]
    max_vfolder_size: Optional[int]
    max_concurrent_sftp_sessions: Optional[int]
    max_session_lifetime: Optional[int]
    total_resource_slots: Optional[ResourceSlot]

    @override
    def build_row(self) -> KeyPairResourcePolicyRow:
        from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow

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
