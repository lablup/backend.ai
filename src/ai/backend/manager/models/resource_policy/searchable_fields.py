"""What a resource policy search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.types import DefaultForUnspecified
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
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _KeyPairResourcePolicyOwnFields(
    RowDataConverter[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]
):
    """The keypair policy's own columns."""

    uuid = SearchableField(
        KeyPairResourcePolicyRow.uuid,
        UUIDConditions(KeyPairResourcePolicyRow.uuid),
        ColumnOrder(KeyPairResourcePolicyRow.uuid),
    )
    name = SearchableField(
        KeyPairResourcePolicyRow.name,
        StringConditions(KeyPairResourcePolicyRow.name),
        ColumnOrder(KeyPairResourcePolicyRow.name),
    )
    created_at = SearchableField(
        KeyPairResourcePolicyRow.created_at,
        DateTimeConditions(KeyPairResourcePolicyRow.created_at),
        ColumnOrder(KeyPairResourcePolicyRow.created_at),
    )
    is_default = SearchableField(
        KeyPairResourcePolicyRow.is_default,
        BoolConditions(KeyPairResourcePolicyRow.is_default),
        ColumnOrder(KeyPairResourcePolicyRow.is_default),
    )
    """Declared, not exposed: which policy an unassigned keypair falls back to."""
    default_for_unspecified = SearchableField(
        KeyPairResourcePolicyRow.default_for_unspecified,
        EnumConditions(KeyPairResourcePolicyRow.default_for_unspecified, DefaultForUnspecified),
        ColumnOrder(KeyPairResourcePolicyRow.default_for_unspecified),
    )
    max_session_lifetime = SearchableField(
        KeyPairResourcePolicyRow.max_session_lifetime,
        IntConditions(KeyPairResourcePolicyRow.max_session_lifetime),
        ColumnOrder(KeyPairResourcePolicyRow.max_session_lifetime),
    )
    max_concurrent_sessions = SearchableField(
        KeyPairResourcePolicyRow.max_concurrent_sessions,
        IntConditions(KeyPairResourcePolicyRow.max_concurrent_sessions),
        ColumnOrder(KeyPairResourcePolicyRow.max_concurrent_sessions),
    )
    max_pending_session_count = SearchableField(
        KeyPairResourcePolicyRow.max_pending_session_count,
        IntConditions(KeyPairResourcePolicyRow.max_pending_session_count),
        ColumnOrder(KeyPairResourcePolicyRow.max_pending_session_count),
    )
    max_priority = SearchableField(
        KeyPairResourcePolicyRow.max_priority,
        IntConditions(KeyPairResourcePolicyRow.max_priority),
        ColumnOrder(KeyPairResourcePolicyRow.max_priority),
    )
    max_concurrent_sftp_sessions = SearchableField(
        KeyPairResourcePolicyRow.max_concurrent_sftp_sessions,
        IntConditions(KeyPairResourcePolicyRow.max_concurrent_sftp_sessions),
        ColumnOrder(KeyPairResourcePolicyRow.max_concurrent_sftp_sessions),
    )
    max_containers_per_session = SearchableField(
        KeyPairResourcePolicyRow.max_containers_per_session,
        IntConditions(KeyPairResourcePolicyRow.max_containers_per_session),
        ColumnOrder(KeyPairResourcePolicyRow.max_containers_per_session),
    )
    idle_timeout = SearchableField(
        KeyPairResourcePolicyRow.idle_timeout,
        IntConditions(KeyPairResourcePolicyRow.idle_timeout),
        ColumnOrder(KeyPairResourcePolicyRow.idle_timeout),
    )
    total_resource_slots = SearchableField(
        KeyPairResourcePolicyRow.total_resource_slots, None, None
    )
    """Impossible: a JSON document of slot names to amounts."""
    max_pending_session_resource_slots = SearchableField(
        KeyPairResourcePolicyRow.max_pending_session_resource_slots, None, None
    )
    """Impossible: a JSON document of slot names to amounts."""
    allowed_vfolder_hosts = SearchableField(
        KeyPairResourcePolicyRow.allowed_vfolder_hosts, None, None
    )
    """Impossible: a JSON document of hosts to permission sets."""

    @override
    def to_data(self, row: KeyPairResourcePolicyRow) -> KeyPairResourcePolicyData:
        return KeyPairResourcePolicyData(
            uuid=self.uuid.read(row),
            name=self.name.read(row),
            created_at=self.created_at.read(row),
            default_for_unspecified=self.default_for_unspecified.read(row),
            total_resource_slots=self.total_resource_slots.read(row),
            max_session_lifetime=self.max_session_lifetime.read(row),
            max_concurrent_sessions=self.max_concurrent_sessions.read(row),
            max_pending_session_count=self.max_pending_session_count.read(row),
            max_priority=self.max_priority.read(row),
            max_pending_session_resource_slots=self.max_pending_session_resource_slots.read(row),
            max_concurrent_sftp_sessions=self.max_concurrent_sftp_sessions.read(row),
            max_containers_per_session=self.max_containers_per_session.read(row),
            idle_timeout=self.idle_timeout.read(row),
            allowed_vfolder_hosts=self.allowed_vfolder_hosts.read(row),
        )


class KeyPairResourcePolicySearchableFields:
    own = _KeyPairResourcePolicyOwnFields()


class _UserResourcePolicyOwnFields(RowDataConverter[UserResourcePolicyRow, UserResourcePolicyData]):
    """The user policy's own columns."""

    uuid = SearchableField(
        UserResourcePolicyRow.uuid,
        UUIDConditions(UserResourcePolicyRow.uuid),
        ColumnOrder(UserResourcePolicyRow.uuid),
    )
    name = SearchableField(
        UserResourcePolicyRow.name,
        StringConditions(UserResourcePolicyRow.name),
        ColumnOrder(UserResourcePolicyRow.name),
    )
    created_at = SearchableField(
        UserResourcePolicyRow.created_at,
        DateTimeConditions(UserResourcePolicyRow.created_at),
        ColumnOrder(UserResourcePolicyRow.created_at),
    )
    max_vfolder_count = SearchableField(
        UserResourcePolicyRow.max_vfolder_count,
        IntConditions(UserResourcePolicyRow.max_vfolder_count),
        ColumnOrder(UserResourcePolicyRow.max_vfolder_count),
    )
    max_quota_scope_size = SearchableField(
        UserResourcePolicyRow.max_quota_scope_size,
        IntConditions(UserResourcePolicyRow.max_quota_scope_size),
        ColumnOrder(UserResourcePolicyRow.max_quota_scope_size),
    )
    max_session_count_per_model_session = SearchableField(
        UserResourcePolicyRow.max_session_count_per_model_session,
        IntConditions(UserResourcePolicyRow.max_session_count_per_model_session),
        ColumnOrder(UserResourcePolicyRow.max_session_count_per_model_session),
    )
    max_customized_image_count = SearchableField(
        UserResourcePolicyRow.max_customized_image_count,
        IntConditions(UserResourcePolicyRow.max_customized_image_count),
        ColumnOrder(UserResourcePolicyRow.max_customized_image_count),
    )
    max_concurrent_logins = SearchableField(
        UserResourcePolicyRow.max_concurrent_logins,
        IntConditions(UserResourcePolicyRow.max_concurrent_logins),
        ColumnOrder(UserResourcePolicyRow.max_concurrent_logins),
    )

    @override
    def to_data(self, row: UserResourcePolicyRow) -> UserResourcePolicyData:
        return UserResourcePolicyData(
            uuid=self.uuid.read(row),
            name=self.name.read(row),
            created_at=self.created_at.read(row),
            max_vfolder_count=self.max_vfolder_count.read(row),
            max_quota_scope_size=self.max_quota_scope_size.read(row),
            max_session_count_per_model_session=self.max_session_count_per_model_session.read(row),
            max_customized_image_count=self.max_customized_image_count.read(row),
            max_concurrent_logins=self.max_concurrent_logins.read(row),
        )


class UserResourcePolicySearchableFields:
    own = _UserResourcePolicyOwnFields()


class _ProjectResourcePolicyOwnFields(
    RowDataConverter[ProjectResourcePolicyRow, ProjectResourcePolicyData]
):
    """The project policy's own columns."""

    uuid = SearchableField(
        ProjectResourcePolicyRow.uuid,
        UUIDConditions(ProjectResourcePolicyRow.uuid),
        ColumnOrder(ProjectResourcePolicyRow.uuid),
    )
    name = SearchableField(
        ProjectResourcePolicyRow.name,
        StringConditions(ProjectResourcePolicyRow.name),
        ColumnOrder(ProjectResourcePolicyRow.name),
    )
    created_at = SearchableField(
        ProjectResourcePolicyRow.created_at,
        DateTimeConditions(ProjectResourcePolicyRow.created_at),
        ColumnOrder(ProjectResourcePolicyRow.created_at),
    )
    max_vfolder_count = SearchableField(
        ProjectResourcePolicyRow.max_vfolder_count,
        IntConditions(ProjectResourcePolicyRow.max_vfolder_count),
        ColumnOrder(ProjectResourcePolicyRow.max_vfolder_count),
    )
    max_quota_scope_size = SearchableField(
        ProjectResourcePolicyRow.max_quota_scope_size,
        IntConditions(ProjectResourcePolicyRow.max_quota_scope_size),
        ColumnOrder(ProjectResourcePolicyRow.max_quota_scope_size),
    )
    max_network_count = SearchableField(
        ProjectResourcePolicyRow.max_network_count,
        IntConditions(ProjectResourcePolicyRow.max_network_count),
        ColumnOrder(ProjectResourcePolicyRow.max_network_count),
    )

    @override
    def to_data(self, row: ProjectResourcePolicyRow) -> ProjectResourcePolicyData:
        return ProjectResourcePolicyData(
            uuid=self.uuid.read(row),
            name=self.name.read(row),
            created_at=self.created_at.read(row),
            max_vfolder_count=self.max_vfolder_count.read(row),
            max_quota_scope_size=self.max_quota_scope_size.read(row),
            max_network_count=self.max_network_count.read(row),
        )


class ProjectResourcePolicySearchableFields:
    own = _ProjectResourcePolicyOwnFields()
