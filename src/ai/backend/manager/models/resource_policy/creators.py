"""Insert specs of the three resource policies — global catalogs keyed by name."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyUUID,
    ProjectResourcePolicyUUID,
    UserResourcePolicyUUID,
)
from ai.backend.common.types import DefaultForUnspecified, ResourceSlot
from ai.backend.manager.data.resource.types import (
    KeyPairResourcePolicyData,
    ProjectResourcePolicyData,
    UserResourcePolicyData,
)
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.specs.creator import GlobalEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class KeyPairResourcePolicyCreator(
    GlobalEntityCreator[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]
):
    name: str
    allowed_vfolder_hosts: dict[str, Any] | None
    default_for_unspecified: DefaultForUnspecified | None
    idle_timeout: int | None
    max_concurrent_sessions: int | None
    max_containers_per_session: int | None
    max_pending_session_count: int | None
    max_pending_session_resource_slots: ResourceSlot | None
    max_priority: int | None
    max_concurrent_sftp_sessions: int | None
    max_session_lifetime: int | None
    total_resource_slots: ResourceSlot | None

    @override
    def entity_id(self, row: KeyPairResourcePolicyRow) -> KeyPairResourcePolicyUUID:
        return KeyPairResourcePolicyUUID(row.uuid)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

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
            max_priority=self.max_priority,
            max_concurrent_sftp_sessions=self.max_concurrent_sftp_sessions,
            max_containers_per_session=self.max_containers_per_session,
            idle_timeout=self.idle_timeout,
            allowed_vfolder_hosts=self.allowed_vfolder_hosts,
        )

    @override
    def to_data(self, row: KeyPairResourcePolicyRow) -> KeyPairResourcePolicyData:
        return row.to_dataclass()


@dataclass
class UserResourcePolicyCreator(GlobalEntityCreator[UserResourcePolicyRow, UserResourcePolicyData]):
    name: str
    max_vfolder_count: int
    max_quota_scope_size: int
    max_session_count_per_model_session: int
    max_customized_image_count: int
    max_concurrent_logins: int | None = None
    max_api_requests_per_window: int | None = None

    @override
    def entity_id(self, row: UserResourcePolicyRow) -> UserResourcePolicyUUID:
        return UserResourcePolicyUUID(row.uuid)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> UserResourcePolicyRow:
        return UserResourcePolicyRow(
            name=self.name,
            max_vfolder_count=self.max_vfolder_count,
            max_quota_scope_size=self.max_quota_scope_size,
            max_session_count_per_model_session=self.max_session_count_per_model_session,
            max_customized_image_count=self.max_customized_image_count,
            max_concurrent_logins=self.max_concurrent_logins,
            max_api_requests_per_window=self.max_api_requests_per_window,
        )

    @override
    def to_data(self, row: UserResourcePolicyRow) -> UserResourcePolicyData:
        return row.to_dataclass()


@dataclass
class ProjectResourcePolicyCreator(
    GlobalEntityCreator[ProjectResourcePolicyRow, ProjectResourcePolicyData]
):
    name: str
    max_vfolder_count: int
    max_quota_scope_size: int
    max_network_count: int

    @override
    def entity_id(self, row: ProjectResourcePolicyRow) -> ProjectResourcePolicyUUID:
        return ProjectResourcePolicyUUID(row.uuid)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> ProjectResourcePolicyRow:
        return ProjectResourcePolicyRow(
            name=self.name,
            max_vfolder_count=self.max_vfolder_count,
            max_quota_scope_size=self.max_quota_scope_size,
            max_network_count=self.max_network_count,
        )

    @override
    def to_data(self, row: ProjectResourcePolicyRow) -> ProjectResourcePolicyData:
        return row.to_dataclass()
