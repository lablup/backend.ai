"""Upsert specs of the three resource policies.

Each is written under its stated uuid. ``name`` is the primary key keypairs, users and
projects refer to, so it is written on insert only.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyUUID,
    ProjectResourcePolicyUUID,
    UserResourcePolicyUUID,
)
from ai.backend.common.types import DefaultForUnspecified, ResourceSlot, VFolderHostPermission
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
from ai.backend.manager.models.resource_policy.searchable_fields import (
    KeyPairResourcePolicySearchableFields,
    ProjectResourcePolicySearchableFields,
    UserResourcePolicySearchableFields,
)
from ai.backend.manager.models.specs.created_in import CreatedInGlobal
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter

__all__ = (
    "KeyPairResourcePolicyUpserter",
    "ProjectResourcePolicyUpserter",
    "UserResourcePolicyUpserter",
)


@dataclass
class KeyPairResourcePolicyUpserter(
    CreatedInGlobal[KeyPairResourcePolicyRow],
    EntityUpserter[KeyPairResourcePolicyRow, KeyPairResourcePolicyData],
):
    """Conflict key: uuid."""

    uuid: KeyPairResourcePolicyUUID
    name: str
    is_default: bool
    default_for_unspecified: DefaultForUnspecified
    total_resource_slots: ResourceSlot
    max_session_lifetime: int
    max_concurrent_sessions: int
    max_pending_session_count: int | None
    max_pending_session_resource_slots: ResourceSlot | None
    max_priority: int | None
    max_concurrent_sftp_sessions: int
    max_containers_per_session: int
    idle_timeout: int
    allowed_vfolder_hosts: Mapping[str, Sequence[VFolderHostPermission]]

    @override
    def entity_id(self, row: KeyPairResourcePolicyRow) -> KeyPairResourcePolicyUUID:
        return KeyPairResourcePolicyUUID(row.uuid)

    @override
    def row_class(self) -> type[KeyPairResourcePolicyRow]:
        return KeyPairResourcePolicyRow

    @override
    def index_elements(self) -> list[str]:
        return ["uuid"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"uuid": self.uuid, "name": self.name, **self._values()}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return self._values()

    def _values(self) -> dict[str, Any]:
        return {
            "is_default": self.is_default,
            "default_for_unspecified": self.default_for_unspecified,
            "total_resource_slots": self.total_resource_slots,
            "max_session_lifetime": self.max_session_lifetime,
            "max_concurrent_sessions": self.max_concurrent_sessions,
            "max_pending_session_count": self.max_pending_session_count,
            "max_pending_session_resource_slots": self.max_pending_session_resource_slots,
            "max_priority": self.max_priority,
            "max_concurrent_sftp_sessions": self.max_concurrent_sftp_sessions,
            "max_containers_per_session": self.max_containers_per_session,
            "idle_timeout": self.idle_timeout,
            "allowed_vfolder_hosts": self.allowed_vfolder_hosts,
        }

    @override
    def to_data(self, row: KeyPairResourcePolicyRow) -> KeyPairResourcePolicyData:
        return KeyPairResourcePolicySearchableFields.own.to_data(row)


@dataclass
class UserResourcePolicyUpserter(
    CreatedInGlobal[UserResourcePolicyRow],
    EntityUpserter[UserResourcePolicyRow, UserResourcePolicyData],
):
    """Conflict key: uuid."""

    uuid: UserResourcePolicyUUID
    name: str
    max_vfolder_count: int
    max_quota_scope_size: int
    max_session_count_per_model_session: int
    max_customized_image_count: int
    max_concurrent_logins: int | None

    @override
    def entity_id(self, row: UserResourcePolicyRow) -> UserResourcePolicyUUID:
        return UserResourcePolicyUUID(row.uuid)

    @override
    def row_class(self) -> type[UserResourcePolicyRow]:
        return UserResourcePolicyRow

    @override
    def index_elements(self) -> list[str]:
        return ["uuid"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"uuid": self.uuid, "name": self.name, **self._values()}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return self._values()

    def _values(self) -> dict[str, Any]:
        return {
            "max_vfolder_count": self.max_vfolder_count,
            "max_quota_scope_size": self.max_quota_scope_size,
            "max_session_count_per_model_session": self.max_session_count_per_model_session,
            "max_customized_image_count": self.max_customized_image_count,
            "max_concurrent_logins": self.max_concurrent_logins,
        }

    @override
    def to_data(self, row: UserResourcePolicyRow) -> UserResourcePolicyData:
        return UserResourcePolicySearchableFields.own.to_data(row)


@dataclass
class ProjectResourcePolicyUpserter(
    CreatedInGlobal[ProjectResourcePolicyRow],
    EntityUpserter[ProjectResourcePolicyRow, ProjectResourcePolicyData],
):
    """Conflict key: uuid."""

    uuid: ProjectResourcePolicyUUID
    name: str
    max_vfolder_count: int
    max_quota_scope_size: int
    max_network_count: int

    @override
    def entity_id(self, row: ProjectResourcePolicyRow) -> ProjectResourcePolicyUUID:
        return ProjectResourcePolicyUUID(row.uuid)

    @override
    def row_class(self) -> type[ProjectResourcePolicyRow]:
        return ProjectResourcePolicyRow

    @override
    def index_elements(self) -> list[str]:
        return ["uuid"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"uuid": self.uuid, "name": self.name, **self._values()}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return self._values()

    def _values(self) -> dict[str, Any]:
        return {
            "max_vfolder_count": self.max_vfolder_count,
            "max_quota_scope_size": self.max_quota_scope_size,
            "max_network_count": self.max_network_count,
        }

    @override
    def to_data(self, row: ProjectResourcePolicyRow) -> ProjectResourcePolicyData:
        return ProjectResourcePolicySearchableFields.own.to_data(row)
