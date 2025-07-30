import msgpack

from ai.backend.common.clients.prometheus.container_util.client import ContainerUtilizationReader
from ai.backend.common.clients.prometheus.container_util.data.request import (
    ContainerUtilizationQueryParameter,
)
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.services.metric.compat.container import transform_container_metrics

from .kernel import KernelRow, KernelStatus
from .resource_usage import BaseResourceUsageGroup, ResourceGroupUnit, parse_resource_usage


async def parse_resource_usage_groups(
    utilization_reader: ContainerUtilizationReader,
    kernels: list[KernelRow],
    valkey_stat_client: ValkeyStatClient,
    config: ManagerUnifiedConfig,
) -> list[BaseResourceUsageGroup]:
    stat_map = {k.id: k.last_stat for k in kernels}

    if config.api.fetch_live_stat_from_redis:
        stat_empty_kerns = [k.id for k in kernels if not k.last_stat]
        kernel_ids_str = [str(kern_id) for kern_id in stat_empty_kerns]
        raw_stats = await valkey_stat_client.get_user_kernel_statistics_batch(kernel_ids_str)
        for kern_id, raw_stat in zip(stat_empty_kerns, raw_stats):
            if raw_stat is None:
                continue
            stat_map[kern_id] = msgpack.unpackb(raw_stat)
    else:
        for k in kernels:
            result = await utilization_reader.get_container_utilization(
                ContainerUtilizationQueryParameter(
                    value_type=None,
                    kernel_id=k.id,
                )
            )
            live_stat = transform_container_metrics(result)
            stat_map[k.id] = live_stat

    return [
        BaseResourceUsageGroup(
            kernel_row=kern,
            project_row=kern.session.group,
            session_row=kern.session,
            created_at=kern.created_at,
            terminated_at=kern.terminated_at,
            scheduled_at=kern.status_history.get(KernelStatus.SCHEDULED.name),
            used_time=kern.used_time,
            used_days=kern.get_used_days(config.system.timezone),
            last_stat=stat_map[kern.id],
            user_id=kern.session.user_uuid,
            user_email=kern.session.user.email,
            access_key=kern.session.access_key,
            project_id=kern.session.group.id if kern.session.group is not None else None,
            project_name=kern.session.group.name if kern.session.group is not None else None,
            kernel_id=kern.id,
            container_ids={kern.container_id},
            session_id=kern.session_id,
            session_name=kern.session.name,
            domain_name=kern.session.domain_name,
            full_name=kern.session.user.full_name,
            images={kern.image},
            agents={kern.agent},
            status=kern.status.name,
            status_history=kern.status_history,
            cluster_mode=kern.cluster_mode,
            status_info=kern.status_info,
            group_unit=ResourceGroupUnit.KERNEL,
            total_usage=parse_resource_usage(kern, stat_map[kern.id]),
        )
        for kern in kernels
    ]
