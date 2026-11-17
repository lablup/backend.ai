"""What a session search can filter and order by, and how a session row becomes data."""

from __future__ import annotations

from typing import override

import sqlalchemy as sa

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.session import SessionEntityType, SessionID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.types import AccessKey, SessionResult, SessionTypes
from ai.backend.manager.data.session.types import SessionEntityData, SessionStatus
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.entity_label.query_spec import (
    EntityLabelCorrelation,
    EntityLabelQuerySpec,
)
from ai.backend.manager.models.kernel.query_spec import KernelQuerySpec
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.kernel_group.row import KernelGroupRow
from ai.backend.manager.models.kernel_group_environ.query_spec import (
    KernelGroupEnvironQuerySpec,
)
from ai.backend.manager.models.kernel_group_environ.row import KernelGroupEnvironRow
from ai.backend.manager.models.kernel_group_resource_slot.query_spec import (
    KernelGroupResourceSlotQuerySpec,
)
from ai.backend.manager.models.kernel_group_resource_slot.row import KernelGroupResourceSlotRow
from ai.backend.manager.models.kernel_group_vfolder_mount.row import KernelGroupVFolderMountRow
from ai.backend.manager.models.network.row import NetworkType
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.string import (
    StringConditions,
    StringEqualityConditions,
)
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation
from ai.backend.manager.models.specs.search.field import NestedQueryColumn, QueryColumn
from ai.backend.manager.models.specs.search.usage import UsedByConditions, UsesConditions


class _SessionOwnColumns(RowDataConverter[SessionRow, SessionEntityData]):
    """The session's own columns."""

    id = QueryColumn(SessionRow.id, UUIDConditions(SessionRow.id), ColumnOrder(SessionRow.id))
    creation_id = QueryColumn(
        SessionRow.creation_id,
        StringConditions(SessionRow.creation_id),
        ColumnOrder(SessionRow.creation_id),
    )
    name = QueryColumn(
        SessionRow.name, StringConditions(SessionRow.name), ColumnOrder(SessionRow.name)
    )
    session_type = QueryColumn(
        SessionRow.session_type,
        EnumConditions(SessionRow.session_type, SessionTypes),
        ColumnOrder(SessionRow.session_type),
    )
    priority = QueryColumn(
        SessionRow.priority, IntConditions(SessionRow.priority), ColumnOrder(SessionRow.priority)
    )
    is_preemptible = QueryColumn(
        SessionRow.is_preemptible,
        BoolConditions(SessionRow.is_preemptible),
        ColumnOrder(SessionRow.is_preemptible),
    )
    job_priority = QueryColumn(
        SessionRow.job_priority,
        IntConditions(SessionRow.job_priority),
        ColumnOrder(SessionRow.job_priority),
    )
    cluster_mode = QueryColumn(
        SessionRow.cluster_mode,
        StringConditions(SessionRow.cluster_mode),
        ColumnOrder(SessionRow.cluster_mode),
    )
    cluster_size = QueryColumn(
        SessionRow.cluster_size,
        IntConditions(SessionRow.cluster_size),
        ColumnOrder(SessionRow.cluster_size),
    )
    options = QueryColumn(SessionRow.options, None, None)
    agent_ids = QueryColumn(SessionRow.agent_ids, None, None)
    session_group_id = QueryColumn(
        SessionRow.session_group_id,
        UUIDConditions(SessionRow.session_group_id),
        ColumnOrder(SessionRow.session_group_id),
    )
    resource_group_id = QueryColumn(
        SessionRow.resource_group_id,
        UUIDConditions(SessionRow.resource_group_id),
        ColumnOrder(SessionRow.resource_group_id),
    )
    resource_group_name = QueryColumn(
        SessionRow.scaling_group_name,
        StringConditions(SessionRow.scaling_group_name),
        ColumnOrder(SessionRow.scaling_group_name),
    )
    target_sgroup_names = QueryColumn(SessionRow.target_sgroup_names, None, None)
    domain_name = QueryColumn(
        SessionRow.domain_name,
        StringConditions(SessionRow.domain_name),
        ColumnOrder(SessionRow.domain_name),
    )
    domain_id = QueryColumn(
        SessionRow.domain_id,
        UUIDConditions(SessionRow.domain_id),
        ColumnOrder(SessionRow.domain_id),
    )
    group_id = QueryColumn(
        SessionRow.group_id, UUIDConditions(SessionRow.group_id), ColumnOrder(SessionRow.group_id)
    )
    user_uuid = QueryColumn(
        SessionRow.user_uuid,
        UUIDConditions(SessionRow.user_uuid),
        ColumnOrder(SessionRow.user_uuid),
    )
    access_key = QueryColumn(
        SessionRow.access_key,
        StringConditions(SessionRow.access_key),
        ColumnOrder(SessionRow.access_key),
    )
    images = QueryColumn(SessionRow.images, None, None)
    image_ids = QueryColumn(SessionRow.image_ids, None, None)
    tag = QueryColumn(SessionRow.tag, StringConditions(SessionRow.tag), ColumnOrder(SessionRow.tag))
    vfolder_mounts = QueryColumn(SessionRow.vfolder_mounts, None, None)
    environ = QueryColumn(SessionRow.environ, None, None)
    bootstrap_script = QueryColumn(SessionRow.bootstrap_script, None, None)
    use_host_network = QueryColumn(
        SessionRow.use_host_network,
        BoolConditions(SessionRow.use_host_network),
        ColumnOrder(SessionRow.use_host_network),
    )
    timeout = QueryColumn(
        SessionRow.timeout, IntConditions(SessionRow.timeout), ColumnOrder(SessionRow.timeout)
    )
    batch_timeout = QueryColumn(
        SessionRow.batch_timeout,
        IntConditions(SessionRow.batch_timeout),
        ColumnOrder(SessionRow.batch_timeout),
    )
    terminated_at = QueryColumn(
        SessionRow.terminated_at,
        DateTimeConditions(SessionRow.terminated_at),
        ColumnOrder(SessionRow.terminated_at),
    )
    starts_at = QueryColumn(
        SessionRow.starts_at,
        DateTimeConditions(SessionRow.starts_at),
        ColumnOrder(SessionRow.starts_at),
    )
    requested_starts_at = QueryColumn(
        SessionRow.requested_starts_at,
        DateTimeConditions(SessionRow.requested_starts_at),
        ColumnOrder(SessionRow.requested_starts_at),
    )
    status = QueryColumn(
        SessionRow.status,
        EnumConditions(SessionRow.status, SessionStatus),
        ColumnOrder(SessionRow.status),
    )
    status_info = QueryColumn(
        SessionRow.status_info,
        StringEqualityConditions(SessionRow.status_info),
        ColumnOrder(SessionRow.status_info),
    )
    status_data = QueryColumn(SessionRow.status_data, None, None)
    status_history = QueryColumn(SessionRow.status_history, None, None)
    callback_url = QueryColumn(SessionRow.callback_url, None, None)
    startup_command = QueryColumn(SessionRow.startup_command, None, None)
    result = QueryColumn(
        SessionRow.result,
        EnumConditions(SessionRow.result, SessionResult),
        ColumnOrder(SessionRow.result),
    )
    num_queries = QueryColumn(
        SessionRow.num_queries,
        IntConditions(SessionRow.num_queries),
        ColumnOrder(SessionRow.num_queries),
    )
    last_stat = QueryColumn(SessionRow.last_stat, None, None)
    network_type = QueryColumn(
        SessionRow.network_type,
        EnumConditions(SessionRow.network_type, NetworkType),
        ColumnOrder(SessionRow.network_type),
    )
    network_id = QueryColumn(
        SessionRow.network_id,
        StringConditions(SessionRow.network_id),
        ColumnOrder(SessionRow.network_id),
    )
    replica_id = QueryColumn(
        SessionRow.replica_id,
        UUIDConditions(SessionRow.replica_id),
        ColumnOrder(SessionRow.replica_id),
    )
    created_at = QueryColumn(
        SessionRow.created_at,
        DateTimeConditions(SessionRow.created_at),
        ColumnOrder(SessionRow.created_at),
    )

    @override
    def to_data(self, row: SessionRow) -> SessionEntityData:
        access_key = self.access_key.read(row)
        return SessionEntityData(
            id=SessionID(self.id.read(row)),
            creation_id=self.creation_id.read(row),
            name=self.name.read(row),
            session_type=self.session_type.read(row),
            priority=self.priority.read(row),
            is_preemptible=self.is_preemptible.read(row),
            job_priority=self.job_priority.read(row),
            cluster_mode=self.cluster_mode.read(row),
            cluster_size=self.cluster_size.read(row),
            options=self.options.read(row),
            agent_ids=self.agent_ids.read(row),
            session_group_id=self.session_group_id.read(row),
            resource_group_id=self.resource_group_id.read(row),
            resource_group_name=self.resource_group_name.read(row),
            target_sgroup_names=self.target_sgroup_names.read(row),
            domain_name=self.domain_name.read(row),
            domain_id=self.domain_id.read(row),
            group_id=self.group_id.read(row),
            user_uuid=self.user_uuid.read(row),
            access_key=AccessKey(access_key) if access_key is not None else None,
            images=self.images.read(row),
            image_ids=self.image_ids.read(row),
            tag=self.tag.read(row),
            vfolder_mounts=self.vfolder_mounts.read(row),
            environ=self.environ.read(row),
            bootstrap_script=self.bootstrap_script.read(row),
            use_host_network=self.use_host_network.read(row),
            timeout=self.timeout.read(row),
            batch_timeout=self.batch_timeout.read(row),
            terminated_at=self.terminated_at.read(row),
            starts_at=self.starts_at.read(row),
            requested_starts_at=self.requested_starts_at.read(row),
            status=self.status.read(row),
            status_info=self.status_info.read(row),
            status_data=self.status_data.read(row),
            status_history=self.status_history.read(row),
            callback_url=self.callback_url.read(row),
            startup_command=self.startup_command.read(row),
            result=self.result.read(row),
            num_queries=self.num_queries.read(row),
            last_stat=self.last_stat.read(row),
            network_type=self.network_type.read(row),
            network_id=self.network_id.read(row),
            replica_id=self.replica_id.read(row),
            created_at=self.created_at.read(row),
        )


class _SessionNestedColumns:
    """Rows of other tables the session owns: labels, kernels and kernel group rows."""

    labels = NestedQueryColumn(
        EntityLabelQuerySpec.own,
        EntityLabelCorrelation(SessionRow, SessionEntityType(), SessionRow.id),
    )
    kernels = NestedQueryColumn(
        KernelQuerySpec.own,
        ToManyCorrelation(KernelRow, SessionRow, KernelRow.session_id == SessionRow.id),
    )
    kernel_group_environ = NestedQueryColumn(
        KernelGroupEnvironQuerySpec.own,
        ToManyCorrelation(
            sa.join(
                KernelGroupEnvironRow,
                KernelGroupRow,
                KernelGroupRow.id == KernelGroupEnvironRow.kernel_group_id,
            ),
            SessionRow,
            KernelGroupRow.session_id == SessionRow.id,
        ),
    )
    kernel_group_resource_slots = NestedQueryColumn(
        KernelGroupResourceSlotQuerySpec.own,
        ToManyCorrelation(
            sa.join(
                KernelGroupResourceSlotRow,
                KernelGroupRow,
                KernelGroupRow.id == KernelGroupResourceSlotRow.kernel_group_id,
            ),
            SessionRow,
            KernelGroupRow.session_id == SessionRow.id,
        ),
    )


class _SessionUsage:
    """Uses between a session and other entities."""

    deployments = UsedByConditions[DeploymentID](
        ToManyCorrelation(RoutingRow, SessionRow, RoutingRow.session == SessionRow.id),
        RoutingRow.endpoint,
    )
    """Sessions a deployment's route rows serve as their replica."""
    images = UsesConditions[ImageID](
        ToManyCorrelation(KernelRow, SessionRow, KernelRow.session_id == SessionRow.id),
        KernelRow.image_id,
    )
    """Sessions whose kernels run the image."""
    agents = UsesConditions[AgentUUID](
        ToManyCorrelation(
            sa.join(KernelRow, AgentRow, AgentRow.id == KernelRow.agent),
            SessionRow,
            KernelRow.session_id == SessionRow.id,
        ),
        AgentRow.uuid,
    )
    """Sessions an agent runs a kernel of."""
    resource_groups = UsesConditions[ResourceGroupID](
        ToManyCorrelation(
            ResourceGroupRow, SessionRow, ResourceGroupRow.id == SessionRow.resource_group_id
        ),
        ResourceGroupRow.id,
    )
    """Sessions a resource group runs."""
    vfolders = UsesConditions[VFolderUUID](
        ToManyCorrelation(
            sa.join(
                KernelGroupVFolderMountRow,
                KernelGroupRow,
                KernelGroupRow.id == KernelGroupVFolderMountRow.kernel_group_id,
            ),
            SessionRow,
            KernelGroupRow.session_id == SessionRow.id,
        ),
        KernelGroupVFolderMountRow.vfolder_id,
    )
    """Sessions whose kernel groups mount the vfolder."""


class _SessionLinkedEntities:
    """How a session connects to other entities; the other entity's permission governs."""

    usage = _SessionUsage


class SessionQuerySpec:
    own = _SessionOwnColumns()
    nested = _SessionNestedColumns
    linked = _SessionLinkedEntities
