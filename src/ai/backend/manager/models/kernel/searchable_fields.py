"""What a kernel search can filter and order by."""

from __future__ import annotations

from typing import override

from ai.backend.common.types import SessionResult, SessionTypes
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.data.kernel.types import (
    ClusterConfig,
    ImageInfo,
    KernelInfo,
    KernelStatus,
    LifecycleStatus,
    Metadata,
    Metrics,
    NetworkConfig,
    RelatedSessionInfo,
    ResourceInfo,
    RuntimeConfig,
    UserPermission,
)
from ai.backend.manager.models.kernel.row import KernelRow
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
from ai.backend.manager.models.specs.search.field import SearchableField


class _KernelOwnFields(RowDataConverter[KernelRow, KernelInfo]):
    """The kernel's own columns a session read reaches."""

    id = SearchableField(KernelRow.id, UUIDConditions(KernelRow.id), ColumnOrder(KernelRow.id))
    session_id = SearchableField(
        KernelRow.session_id,
        UUIDConditions(KernelRow.session_id),
        ColumnOrder(KernelRow.session_id),
    )
    session_creation_id = SearchableField(
        KernelRow.session_creation_id,
        StringConditions(KernelRow.session_creation_id),
        ColumnOrder(KernelRow.session_creation_id),
    )
    session_name = SearchableField(
        KernelRow.session_name,
        StringConditions(KernelRow.session_name),
        ColumnOrder(KernelRow.session_name),
    )
    session_type = SearchableField(
        KernelRow.session_type,
        EnumConditions(KernelRow.session_type, SessionTypes),
        ColumnOrder(KernelRow.session_type),
    )
    status = SearchableField(
        KernelRow.status,
        EnumConditions(KernelRow.status, KernelStatus),
        ColumnOrder(KernelRow.status),
    )
    agent = SearchableField(
        KernelRow.agent, StringConditions(KernelRow.agent), ColumnOrder(KernelRow.agent)
    )
    agent_addr = SearchableField(
        KernelRow.agent_addr,
        StringConditions(KernelRow.agent_addr),
        ColumnOrder(KernelRow.agent_addr),
    )
    cluster_mode = SearchableField(
        KernelRow.cluster_mode,
        StringConditions(KernelRow.cluster_mode),
        ColumnOrder(KernelRow.cluster_mode),
    )
    cluster_size = SearchableField(
        KernelRow.cluster_size,
        IntConditions(KernelRow.cluster_size),
        ColumnOrder(KernelRow.cluster_size),
    )
    cluster_role = SearchableField(
        KernelRow.cluster_role,
        StringConditions(KernelRow.cluster_role),
        ColumnOrder(KernelRow.cluster_role),
    )
    cluster_idx = SearchableField(
        KernelRow.cluster_idx,
        IntConditions(KernelRow.cluster_idx),
        ColumnOrder(KernelRow.cluster_idx),
    )
    local_rank = SearchableField(
        KernelRow.local_rank,
        IntConditions(KernelRow.local_rank),
        ColumnOrder(KernelRow.local_rank),
    )
    cluster_hostname = SearchableField(
        KernelRow.cluster_hostname,
        StringConditions(KernelRow.cluster_hostname),
        ColumnOrder(KernelRow.cluster_hostname),
    )
    uid = SearchableField(KernelRow.uid, IntConditions(KernelRow.uid), ColumnOrder(KernelRow.uid))
    main_gid = SearchableField(
        KernelRow.main_gid, IntConditions(KernelRow.main_gid), ColumnOrder(KernelRow.main_gid)
    )
    gids = SearchableField(KernelRow.gids, None, None)
    resource_group_name = SearchableField(
        KernelRow.scaling_group,
        StringConditions(KernelRow.scaling_group),
        ColumnOrder(KernelRow.scaling_group),
    )
    resource_group_id = SearchableField(
        KernelRow.resource_group_id,
        UUIDConditions(KernelRow.resource_group_id),
        ColumnOrder(KernelRow.resource_group_id),
    )
    domain_name = SearchableField(
        KernelRow.domain_name,
        StringConditions(KernelRow.domain_name),
        ColumnOrder(KernelRow.domain_name),
    )
    group_id = SearchableField(
        KernelRow.group_id, UUIDConditions(KernelRow.group_id), ColumnOrder(KernelRow.group_id)
    )
    user_uuid = SearchableField(
        KernelRow.user_uuid, UUIDConditions(KernelRow.user_uuid), ColumnOrder(KernelRow.user_uuid)
    )
    access_key = SearchableField(
        KernelRow.access_key,
        StringConditions(KernelRow.access_key),
        ColumnOrder(KernelRow.access_key),
    )
    image = SearchableField(
        KernelRow.image, StringConditions(KernelRow.image), ColumnOrder(KernelRow.image)
    )
    image_id = SearchableField(
        KernelRow.image_id, UUIDConditions(KernelRow.image_id), ColumnOrder(KernelRow.image_id)
    )
    architecture = SearchableField(
        KernelRow.architecture,
        StringConditions(KernelRow.architecture),
        ColumnOrder(KernelRow.architecture),
    )
    registry = SearchableField(
        KernelRow.registry, StringConditions(KernelRow.registry), ColumnOrder(KernelRow.registry)
    )
    tag = SearchableField(
        KernelRow.tag, StringConditions(KernelRow.tag), ColumnOrder(KernelRow.tag)
    )
    container_id = SearchableField(
        KernelRow.container_id,
        StringConditions(KernelRow.container_id),
        ColumnOrder(KernelRow.container_id),
    )
    occupied_shares = SearchableField(KernelRow.occupied_shares, None, None)
    environ = SearchableField(KernelRow.environ, None, None)
    mounts = SearchableField(KernelRow.mounts, None, None)
    mount_map = SearchableField(KernelRow.mount_map, None, None)
    vfolder_mounts = SearchableField(KernelRow.vfolder_mounts, None, None)
    attached_devices = SearchableField(KernelRow.attached_devices, None, None)
    resource_opts = SearchableField(KernelRow.resource_opts, None, None)
    bootstrap_script = SearchableField(KernelRow.bootstrap_script, None, None)
    kernel_host = SearchableField(
        KernelRow.kernel_host,
        StringConditions(KernelRow.kernel_host),
        ColumnOrder(KernelRow.kernel_host),
    )
    repl_in_port = SearchableField(
        KernelRow.repl_in_port,
        IntConditions(KernelRow.repl_in_port),
        ColumnOrder(KernelRow.repl_in_port),
    )
    repl_out_port = SearchableField(
        KernelRow.repl_out_port,
        IntConditions(KernelRow.repl_out_port),
        ColumnOrder(KernelRow.repl_out_port),
    )
    stdin_port = SearchableField(
        KernelRow.stdin_port,
        IntConditions(KernelRow.stdin_port),
        ColumnOrder(KernelRow.stdin_port),
    )
    stdout_port = SearchableField(
        KernelRow.stdout_port,
        IntConditions(KernelRow.stdout_port),
        ColumnOrder(KernelRow.stdout_port),
    )
    service_ports = SearchableField(KernelRow.service_ports, None, None)
    preopen_ports = SearchableField(KernelRow.preopen_ports, None, None)
    use_host_network = SearchableField(
        KernelRow.use_host_network,
        BoolConditions(KernelRow.use_host_network),
        ColumnOrder(KernelRow.use_host_network),
    )
    starts_at = SearchableField(
        KernelRow.starts_at,
        DateTimeConditions(KernelRow.starts_at),
        ColumnOrder(KernelRow.starts_at),
    )
    terminated_at = SearchableField(
        KernelRow.terminated_at,
        DateTimeConditions(KernelRow.terminated_at),
        ColumnOrder(KernelRow.terminated_at),
    )
    status_changed = SearchableField(
        KernelRow.status_changed,
        DateTimeConditions(KernelRow.status_changed),
        ColumnOrder(KernelRow.status_changed),
    )
    status_info = SearchableField(
        KernelRow.status_info,
        StringEqualityConditions(KernelRow.status_info),
        ColumnOrder(KernelRow.status_info),
    )
    status_data = SearchableField(KernelRow.status_data, None, None)
    status_history = SearchableField(KernelRow.status_history, None, None)
    callback_url = SearchableField(KernelRow.callback_url, None, None)
    startup_command = SearchableField(KernelRow.startup_command, None, None)
    result = SearchableField(
        KernelRow.result,
        EnumConditions(KernelRow.result, SessionResult),
        ColumnOrder(KernelRow.result),
    )
    internal_data = SearchableField(KernelRow.internal_data, None, None)
    container_log = SearchableField(KernelRow.container_log, None, None)
    num_queries = SearchableField(
        KernelRow.num_queries,
        IntConditions(KernelRow.num_queries),
        ColumnOrder(KernelRow.num_queries),
    )
    last_stat = SearchableField(KernelRow.last_stat, None, None)
    last_seen = SearchableField(
        KernelRow.last_seen,
        DateTimeConditions(KernelRow.last_seen),
        ColumnOrder(KernelRow.last_seen),
    )
    last_observed_at = SearchableField(
        KernelRow.last_observed_at,
        DateTimeConditions(KernelRow.last_observed_at),
        ColumnOrder(KernelRow.last_observed_at),
    )
    created_at = SearchableField(
        KernelRow.created_at,
        DateTimeConditions(KernelRow.created_at),
        ColumnOrder(KernelRow.created_at),
    )

    @override
    def to_data(self, row: KernelRow) -> KernelInfo:
        canonical = self.image.read(row)
        architecture = self.architecture.read(row)
        vfolder_mounts = self.vfolder_mounts.read(row)
        callback_url = self.callback_url.read(row)
        return KernelInfo(
            id=self.id.read(row),
            session=RelatedSessionInfo(
                session_id=str(self.session_id.read(row)),
                creation_id=self.session_creation_id.read(row),
                name=self.session_name.read(row),
                session_type=self.session_type.read(row),
            ),
            user_permission=UserPermission(
                user_uuid=self.user_uuid.read(row),
                access_key=self.access_key.read(row) or "",
                domain_name=self.domain_name.read(row),
                group_id=self.group_id.read(row),
                uid=self.uid.read(row),
                main_gid=self.main_gid.read(row),
                gids=self.gids.read(row),
            ),
            image=ImageInfo(
                image_id=self.image_id.read(row),
                identifier=ImageIdentifier(
                    canonical=canonical,
                    architecture=architecture or "",
                )
                if canonical
                else None,
                registry=self.registry.read(row),
                tag=self.tag.read(row),
                architecture=architecture,
            ),
            network=NetworkConfig(
                kernel_host=self.kernel_host.read(row),
                repl_in_port=self.repl_in_port.read(row),
                repl_out_port=self.repl_out_port.read(row),
                stdin_port=self.stdin_port.read(row),
                stdout_port=self.stdout_port.read(row),
                service_ports=self.service_ports.read(row),
                preopen_ports=self.preopen_ports.read(row),
                use_host_network=self.use_host_network.read(row),
            ),
            cluster=ClusterConfig(
                cluster_mode=self.cluster_mode.read(row),
                cluster_size=self.cluster_size.read(row),
                cluster_role=self.cluster_role.read(row),
                cluster_idx=self.cluster_idx.read(row),
                local_rank=self.local_rank.read(row),
                cluster_hostname=self.cluster_hostname.read(row),
            ),
            resource=ResourceInfo(
                resource_group=self.resource_group_name.read(row),
                resource_group_id=self.resource_group_id.read(row),
                agent=self.agent.read(row),
                agent_addr=self.agent_addr.read(row),
                container_id=self.container_id.read(row),
                occupied_shares=self.occupied_shares.read(row),
                attached_devices=self.attached_devices.read(row) or {},
                resource_opts=self.resource_opts.read(row) or {},
            ),
            runtime=RuntimeConfig(
                environ=self.environ.read(row),
                mounts=self.mounts.read(row),
                mount_map=self.mount_map.read(row),
                vfolder_mounts=[m.to_json() for m in vfolder_mounts] if vfolder_mounts else None,
                bootstrap_script=self.bootstrap_script.read(row),
                startup_command=self.startup_command.read(row),
            ),
            lifecycle=LifecycleStatus(
                status=self.status.read(row),
                result=self.result.read(row),
                created_at=self.created_at.read(row),
                terminated_at=self.terminated_at.read(row),
                starts_at=self.starts_at.read(row),
                status_changed=self.status_changed.read(row),
                status_info=self.status_info.read(row),
                status_data=self.status_data.read(row),
                status_history=self.status_history.read(row),
                last_seen=self.last_seen.read(row),
                last_observed_at=self.last_observed_at.read(row),
            ),
            metrics=Metrics(
                num_queries=self.num_queries.read(row) or 0,
                last_stat=self.last_stat.read(row),
                container_log=self.container_log.read(row),
            ),
            metadata=Metadata(
                callback_url=str(callback_url) if callback_url else None,
                internal_data=self.internal_data.read(row),
            ),
        )


class KernelSearchableFields:
    own = _KernelOwnFields()
