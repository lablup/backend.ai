from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

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
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class KeyPairResourcePolicyUpdater(
    DataUpdater[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]
):
    policy_id: KeyPairResourcePolicyUUID
    allowed_vfolder_hosts: OptionalState[dict[str, Any]] = field(default_factory=OptionalState.nop)
    default_for_unspecified: OptionalState[DefaultForUnspecified] = field(
        default_factory=OptionalState.nop
    )
    idle_timeout: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_concurrent_sessions: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_containers_per_session: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_pending_session_count: TriState[int] = field(default_factory=TriState.nop)
    max_pending_session_resource_slots: TriState[ResourceSlot] = field(default_factory=TriState.nop)
    max_priority: TriState[int] = field(default_factory=TriState.nop)
    max_quota_scope_size: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_vfolder_count: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_vfolder_size: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_concurrent_sftp_sessions: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_session_lifetime: OptionalState[int] = field(default_factory=OptionalState.nop)
    total_resource_slots: OptionalState[ResourceSlot] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[KeyPairResourcePolicyRow]:
        return KeyPairResourcePolicyRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return KeyPairResourcePolicyRow.uuid

    @override
    def target_id_value(self) -> UUID:
        return self.policy_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.allowed_vfolder_hosts.update_dict(to_update, "allowed_vfolder_hosts")
        self.default_for_unspecified.update_dict(to_update, "default_for_unspecified")
        self.idle_timeout.update_dict(to_update, "idle_timeout")
        self.max_concurrent_sessions.update_dict(to_update, "max_concurrent_sessions")
        self.max_containers_per_session.update_dict(to_update, "max_containers_per_session")
        self.max_pending_session_count.update_dict(to_update, "max_pending_session_count")
        self.max_pending_session_resource_slots.update_dict(
            to_update, "max_pending_session_resource_slots"
        )
        self.max_priority.update_dict(to_update, "max_priority")
        self.max_quota_scope_size.update_dict(to_update, "max_quota_scope_size")
        self.max_vfolder_count.update_dict(to_update, "max_vfolder_count")
        self.max_vfolder_size.update_dict(to_update, "max_vfolder_size")
        self.max_concurrent_sftp_sessions.update_dict(to_update, "max_concurrent_sftp_sessions")
        self.max_session_lifetime.update_dict(to_update, "max_session_lifetime")
        self.total_resource_slots.update_dict(to_update, "total_resource_slots")
        return to_update

    @override
    def to_data(self, row: KeyPairResourcePolicyRow) -> KeyPairResourcePolicyData:
        return row.to_dataclass()


@dataclass
class UserResourcePolicyUpdater(DataUpdater[UserResourcePolicyRow, UserResourcePolicyData]):
    policy_id: UserResourcePolicyUUID
    max_vfolder_count: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    max_quota_scope_size: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    max_session_count_per_model_session: OptionalState[int] = field(
        default_factory=OptionalState[int].nop
    )
    max_customized_image_count: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    max_concurrent_logins: TriState[int] = field(default_factory=TriState[int].nop)

    @property
    @override
    def row_class(self) -> type[UserResourcePolicyRow]:
        return UserResourcePolicyRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return UserResourcePolicyRow.uuid

    @override
    def target_id_value(self) -> UUID:
        return self.policy_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.max_vfolder_count.update_dict(to_update, "max_vfolder_count")
        self.max_quota_scope_size.update_dict(to_update, "max_quota_scope_size")
        self.max_session_count_per_model_session.update_dict(
            to_update, "max_session_count_per_model_session"
        )
        self.max_customized_image_count.update_dict(to_update, "max_customized_image_count")
        self.max_concurrent_logins.update_dict(to_update, "max_concurrent_logins")
        return to_update

    @override
    def to_data(self, row: UserResourcePolicyRow) -> UserResourcePolicyData:
        return row.to_dataclass()


@dataclass
class ProjectResourcePolicyUpdater(
    DataUpdater[ProjectResourcePolicyRow, ProjectResourcePolicyData]
):
    policy_id: ProjectResourcePolicyUUID
    max_vfolder_count: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    max_quota_scope_size: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    max_vfolder_size: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    max_network_count: OptionalState[int] = field(default_factory=OptionalState[int].nop)

    @property
    @override
    def row_class(self) -> type[ProjectResourcePolicyRow]:
        return ProjectResourcePolicyRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ProjectResourcePolicyRow.uuid

    @override
    def target_id_value(self) -> UUID:
        return self.policy_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.max_vfolder_count.update_dict(to_update, "max_vfolder_count")
        self.max_quota_scope_size.update_dict(to_update, "max_quota_scope_size")
        self.max_vfolder_size.update_dict(to_update, "max_vfolder_size")
        self.max_network_count.update_dict(to_update, "max_network_count")
        return to_update

    @override
    def to_data(self, row: ProjectResourcePolicyRow) -> ProjectResourcePolicyData:
        return row.to_dataclass()
