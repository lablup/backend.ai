"""What a usage history search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.resource_usage_history.types import (
    DomainUsageBucketData,
    KernelUsageRecordData,
    ProjectUsageBucketData,
    UserUsageBucketData,
)
from ai.backend.manager.models.resource_usage_history.row import (
    DomainUsageBucketRow,
    KernelUsageRecordRow,
    ProjectUsageBucketRow,
    UserUsageBucketRow,
)
from ai.backend.manager.models.specs.conditions.date import DateConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _KernelUsageRecordOwnFields(RowDataConverter[KernelUsageRecordRow, KernelUsageRecordData]):
    """The kernel usage record's own columns."""

    id = SearchableField(
        KernelUsageRecordRow.id,
        UUIDConditions(KernelUsageRecordRow.id),
        ColumnOrder(KernelUsageRecordRow.id),
    )
    kernel_id = SearchableField(
        KernelUsageRecordRow.kernel_id,
        UUIDConditions(KernelUsageRecordRow.kernel_id),
        ColumnOrder(KernelUsageRecordRow.kernel_id),
    )
    session_id = SearchableField(
        KernelUsageRecordRow.session_id,
        UUIDConditions(KernelUsageRecordRow.session_id),
        ColumnOrder(KernelUsageRecordRow.session_id),
    )
    user_uuid = SearchableField(
        KernelUsageRecordRow.user_uuid,
        UUIDConditions(KernelUsageRecordRow.user_uuid),
        ColumnOrder(KernelUsageRecordRow.user_uuid),
    )
    project_id = SearchableField(
        KernelUsageRecordRow.project_id,
        UUIDConditions(KernelUsageRecordRow.project_id),
        ColumnOrder(KernelUsageRecordRow.project_id),
    )
    domain_name = SearchableField(
        KernelUsageRecordRow.domain_name,
        StringConditions(KernelUsageRecordRow.domain_name),
        ColumnOrder(KernelUsageRecordRow.domain_name),
    )
    resource_group = SearchableField(
        KernelUsageRecordRow.resource_group,
        StringConditions(KernelUsageRecordRow.resource_group),
        ColumnOrder(KernelUsageRecordRow.resource_group),
    )
    resource_group_id = SearchableField(
        KernelUsageRecordRow.resource_group_id,
        UUIDConditions(KernelUsageRecordRow.resource_group_id),
        ColumnOrder(KernelUsageRecordRow.resource_group_id),
    )
    period_start = SearchableField(
        KernelUsageRecordRow.period_start,
        DateTimeConditions(KernelUsageRecordRow.period_start),
        ColumnOrder(KernelUsageRecordRow.period_start),
    )
    period_end = SearchableField(
        KernelUsageRecordRow.period_end,
        DateTimeConditions(KernelUsageRecordRow.period_end),
        ColumnOrder(KernelUsageRecordRow.period_end),
    )
    resource_usage = SearchableField(KernelUsageRecordRow.resource_usage, None, None)
    """Impossible: a JSONB document of slot names to resource-seconds."""

    @override
    def to_data(self, row: KernelUsageRecordRow) -> KernelUsageRecordData:
        return KernelUsageRecordData(
            id=self.id.read(row),
            kernel_id=self.kernel_id.read(row),
            session_id=self.session_id.read(row),
            user_uuid=self.user_uuid.read(row),
            project_id=self.project_id.read(row),
            domain_name=self.domain_name.read(row),
            resource_group=self.resource_group.read(row),
            resource_group_id=self.resource_group_id.read(row),
            period_start=self.period_start.read(row),
            period_end=self.period_end.read(row),
            resource_usage=self.resource_usage.read(row),
        )


class KernelUsageRecordSearchableFields:
    own = _KernelUsageRecordOwnFields()


class _DomainUsageBucketOwnFields(RowDataConverter[DomainUsageBucketRow, DomainUsageBucketData]):
    """The domain usage bucket's own columns."""

    id = SearchableField(
        DomainUsageBucketRow.id,
        UUIDConditions(DomainUsageBucketRow.id),
        ColumnOrder(DomainUsageBucketRow.id),
    )
    domain_name = SearchableField(
        DomainUsageBucketRow.domain_name,
        StringConditions(DomainUsageBucketRow.domain_name),
        ColumnOrder(DomainUsageBucketRow.domain_name),
    )
    resource_group = SearchableField(
        DomainUsageBucketRow.resource_group,
        StringConditions(DomainUsageBucketRow.resource_group),
        ColumnOrder(DomainUsageBucketRow.resource_group),
    )
    resource_group_id = SearchableField(
        DomainUsageBucketRow.resource_group_id,
        UUIDConditions(DomainUsageBucketRow.resource_group_id),
        ColumnOrder(DomainUsageBucketRow.resource_group_id),
    )
    period_start = SearchableField(
        DomainUsageBucketRow.period_start,
        DateConditions(DomainUsageBucketRow.period_start),
        ColumnOrder(DomainUsageBucketRow.period_start),
    )
    period_end = SearchableField(
        DomainUsageBucketRow.period_end,
        DateConditions(DomainUsageBucketRow.period_end),
        ColumnOrder(DomainUsageBucketRow.period_end),
    )
    decay_unit_days = SearchableField(
        DomainUsageBucketRow.decay_unit_days,
        IntConditions(DomainUsageBucketRow.decay_unit_days),
        ColumnOrder(DomainUsageBucketRow.decay_unit_days),
    )
    resource_usage = SearchableField(DomainUsageBucketRow.resource_usage, None, None)
    """Impossible: a JSONB document of slot names to resource-seconds."""
    capacity_snapshot = SearchableField(DomainUsageBucketRow.capacity_snapshot, None, None)
    """Impossible: a JSONB document of slot names to capacity."""
    created_at = SearchableField(
        DomainUsageBucketRow.created_at,
        DateTimeConditions(DomainUsageBucketRow.created_at),
        ColumnOrder(DomainUsageBucketRow.created_at),
    )
    updated_at = SearchableField(
        DomainUsageBucketRow.updated_at,
        DateTimeConditions(DomainUsageBucketRow.updated_at),
        ColumnOrder(DomainUsageBucketRow.updated_at),
    )

    @override
    def to_data(self, row: DomainUsageBucketRow) -> DomainUsageBucketData:
        return DomainUsageBucketData(
            id=self.id.read(row),
            domain_name=self.domain_name.read(row),
            resource_group=self.resource_group.read(row),
            resource_group_id=self.resource_group_id.read(row),
            period_start=self.period_start.read(row),
            period_end=self.period_end.read(row),
            decay_unit_days=self.decay_unit_days.read(row),
            resource_usage=self.resource_usage.read(row),
            capacity_snapshot=self.capacity_snapshot.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class DomainUsageBucketSearchableFields:
    own = _DomainUsageBucketOwnFields()


class _ProjectUsageBucketOwnFields(RowDataConverter[ProjectUsageBucketRow, ProjectUsageBucketData]):
    """The project usage bucket's own columns."""

    id = SearchableField(
        ProjectUsageBucketRow.id,
        UUIDConditions(ProjectUsageBucketRow.id),
        ColumnOrder(ProjectUsageBucketRow.id),
    )
    project_id = SearchableField(
        ProjectUsageBucketRow.project_id,
        UUIDConditions(ProjectUsageBucketRow.project_id),
        ColumnOrder(ProjectUsageBucketRow.project_id),
    )
    domain_name = SearchableField(
        ProjectUsageBucketRow.domain_name,
        StringConditions(ProjectUsageBucketRow.domain_name),
        ColumnOrder(ProjectUsageBucketRow.domain_name),
    )
    resource_group = SearchableField(
        ProjectUsageBucketRow.resource_group,
        StringConditions(ProjectUsageBucketRow.resource_group),
        ColumnOrder(ProjectUsageBucketRow.resource_group),
    )
    resource_group_id = SearchableField(
        ProjectUsageBucketRow.resource_group_id,
        UUIDConditions(ProjectUsageBucketRow.resource_group_id),
        ColumnOrder(ProjectUsageBucketRow.resource_group_id),
    )
    period_start = SearchableField(
        ProjectUsageBucketRow.period_start,
        DateConditions(ProjectUsageBucketRow.period_start),
        ColumnOrder(ProjectUsageBucketRow.period_start),
    )
    period_end = SearchableField(
        ProjectUsageBucketRow.period_end,
        DateConditions(ProjectUsageBucketRow.period_end),
        ColumnOrder(ProjectUsageBucketRow.period_end),
    )
    decay_unit_days = SearchableField(
        ProjectUsageBucketRow.decay_unit_days,
        IntConditions(ProjectUsageBucketRow.decay_unit_days),
        ColumnOrder(ProjectUsageBucketRow.decay_unit_days),
    )
    resource_usage = SearchableField(ProjectUsageBucketRow.resource_usage, None, None)
    """Impossible: a JSONB document of slot names to resource-seconds."""
    capacity_snapshot = SearchableField(ProjectUsageBucketRow.capacity_snapshot, None, None)
    """Impossible: a JSONB document of slot names to capacity."""
    created_at = SearchableField(
        ProjectUsageBucketRow.created_at,
        DateTimeConditions(ProjectUsageBucketRow.created_at),
        ColumnOrder(ProjectUsageBucketRow.created_at),
    )
    updated_at = SearchableField(
        ProjectUsageBucketRow.updated_at,
        DateTimeConditions(ProjectUsageBucketRow.updated_at),
        ColumnOrder(ProjectUsageBucketRow.updated_at),
    )

    @override
    def to_data(self, row: ProjectUsageBucketRow) -> ProjectUsageBucketData:
        return ProjectUsageBucketData(
            id=self.id.read(row),
            project_id=self.project_id.read(row),
            domain_name=self.domain_name.read(row),
            resource_group=self.resource_group.read(row),
            resource_group_id=self.resource_group_id.read(row),
            period_start=self.period_start.read(row),
            period_end=self.period_end.read(row),
            decay_unit_days=self.decay_unit_days.read(row),
            resource_usage=self.resource_usage.read(row),
            capacity_snapshot=self.capacity_snapshot.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class ProjectUsageBucketSearchableFields:
    own = _ProjectUsageBucketOwnFields()


class _UserUsageBucketOwnFields(RowDataConverter[UserUsageBucketRow, UserUsageBucketData]):
    """The user usage bucket's own columns."""

    id = SearchableField(
        UserUsageBucketRow.id,
        UUIDConditions(UserUsageBucketRow.id),
        ColumnOrder(UserUsageBucketRow.id),
    )
    user_uuid = SearchableField(
        UserUsageBucketRow.user_uuid,
        UUIDConditions(UserUsageBucketRow.user_uuid),
        ColumnOrder(UserUsageBucketRow.user_uuid),
    )
    project_id = SearchableField(
        UserUsageBucketRow.project_id,
        UUIDConditions(UserUsageBucketRow.project_id),
        ColumnOrder(UserUsageBucketRow.project_id),
    )
    domain_name = SearchableField(
        UserUsageBucketRow.domain_name,
        StringConditions(UserUsageBucketRow.domain_name),
        ColumnOrder(UserUsageBucketRow.domain_name),
    )
    resource_group = SearchableField(
        UserUsageBucketRow.resource_group,
        StringConditions(UserUsageBucketRow.resource_group),
        ColumnOrder(UserUsageBucketRow.resource_group),
    )
    resource_group_id = SearchableField(
        UserUsageBucketRow.resource_group_id,
        UUIDConditions(UserUsageBucketRow.resource_group_id),
        ColumnOrder(UserUsageBucketRow.resource_group_id),
    )
    period_start = SearchableField(
        UserUsageBucketRow.period_start,
        DateConditions(UserUsageBucketRow.period_start),
        ColumnOrder(UserUsageBucketRow.period_start),
    )
    period_end = SearchableField(
        UserUsageBucketRow.period_end,
        DateConditions(UserUsageBucketRow.period_end),
        ColumnOrder(UserUsageBucketRow.period_end),
    )
    decay_unit_days = SearchableField(
        UserUsageBucketRow.decay_unit_days,
        IntConditions(UserUsageBucketRow.decay_unit_days),
        ColumnOrder(UserUsageBucketRow.decay_unit_days),
    )
    resource_usage = SearchableField(UserUsageBucketRow.resource_usage, None, None)
    """Impossible: a JSONB document of slot names to resource-seconds."""
    capacity_snapshot = SearchableField(UserUsageBucketRow.capacity_snapshot, None, None)
    """Impossible: a JSONB document of slot names to capacity."""
    created_at = SearchableField(
        UserUsageBucketRow.created_at,
        DateTimeConditions(UserUsageBucketRow.created_at),
        ColumnOrder(UserUsageBucketRow.created_at),
    )
    updated_at = SearchableField(
        UserUsageBucketRow.updated_at,
        DateTimeConditions(UserUsageBucketRow.updated_at),
        ColumnOrder(UserUsageBucketRow.updated_at),
    )

    @override
    def to_data(self, row: UserUsageBucketRow) -> UserUsageBucketData:
        return UserUsageBucketData(
            id=self.id.read(row),
            user_uuid=self.user_uuid.read(row),
            project_id=self.project_id.read(row),
            domain_name=self.domain_name.read(row),
            resource_group=self.resource_group.read(row),
            resource_group_id=self.resource_group_id.read(row),
            period_start=self.period_start.read(row),
            period_end=self.period_end.read(row),
            decay_unit_days=self.decay_unit_days.read(row),
            resource_usage=self.resource_usage.read(row),
            capacity_snapshot=self.capacity_snapshot.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class UserUsageBucketSearchableFields:
    own = _UserUsageBucketOwnFields()
