import asyncio
from dataclasses import dataclass
from typing import override

from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)

from ...bgtask.tags import PRIVILEGED_WORKER_TAG
from ..config import StorageProxyPrivilegedWorkerConfig
from .stage.bgtask import (
    BgtaskManagerProvisioner,
    BgtaskManagerResult,
    BgtaskManagerSpec,
    BgtaskManagerSpecGenerator,
    BgtaskManagerStage,
)
from .stage.etcd import (
    EtcdProvisioner,
    EtcdResult,
    EtcdSpec,
    EtcdSpecGenerator,
    EtcdStage,
)
from .stage.event_dispatcher import (
    EventDispatcherProvisioner,
    EventDispatcherResult,
    EventDispatcherSpec,
    EventDispatcherSpecGenerator,
    EventDispatcherStage,
)
from .stage.event_registry import (
    EventRegistryProvisioner,
    EventRegistrySpec,
    EventRegistrySpecGenerator,
    EventRegistryStage,
)
from .stage.logger import (
    LoggerProvisioner,
    LoggerResult,
    LoggerSpec,
    LoggerSpecGenerator,
    LoggerStage,
)
from .stage.message_queue import (
    MessageQueueProvisioner,
    MessageQueueResult,
    MessageQueueSpec,
    MessageQueueSpecGenerator,
    MessageQueueStage,
)
from .stage.monitor import (
    MonitorProvisioner,
    MonitorResult,
    MonitorSpec,
    MonitorSpecGenerator,
    MonitorStage,
)
from .stage.redis_config import (
    RedisConfigProvisioner,
    RedisConfigResult,
    RedisConfigSpec,
    RedisConfigSpecGenerator,
    RedisConfigStage,
)
from .stage.valkey_client import (
    ValkeyClientProvisioner,
    ValkeyClientResult,
    ValkeyClientSpec,
    ValkeyClientSpecGenerator,
    ValkeyClientStage,
)
from .stage.volume_pool import (
    VolumePoolProvisioner,
    VolumePoolResult,
    VolumePoolSpec,
    VolumePoolSpecGenerator,
    VolumePoolStage,
)


@dataclass
class BootstrapSpec:
    loop: asyncio.AbstractEventLoop
    local_config: StorageProxyPrivilegedWorkerConfig
    pidx: int


class BootstrapSpecGenerator(ArgsSpecGenerator[BootstrapSpec]):
    pass


@dataclass
class BootstrapResult:
    logger: LoggerResult
    monitor: MonitorResult
    etcd: EtcdResult
    redis_config: RedisConfigResult
    message_queue: MessageQueueResult
    event_dispatcher: EventDispatcherResult
    valkey_client: ValkeyClientResult
    volume_pool: VolumePoolResult
    bgtask_manager: BgtaskManagerResult


class BootstrapProvisioner(Provisioner[BootstrapSpec, BootstrapResult]):
    @property
    @override
    def name(self) -> str:
        return "storage-worker-bootstrap"

    @override
    async def setup(self, spec: BootstrapSpec) -> BootstrapResult:
        local_config = spec.local_config
        sub_logger_stage = LoggerStage(LoggerProvisioner())
        sub_logger_spec = LoggerSpec(
            is_master=False,
            ipc_base_path=local_config.storage_proxy.ipc_base_path,
            config=spec.local_config.logging,
        )
        await sub_logger_stage.setup(LoggerSpecGenerator(sub_logger_spec))
        logger_result = await sub_logger_stage.wait_for_resource()

        monitor_stage = MonitorStage(MonitorProvisioner())
        monitor_spec = MonitorSpec(loop=spec.loop, pidx=spec.pidx, local_config=local_config)
        await monitor_stage.setup(MonitorSpecGenerator(monitor_spec))
        monitor_result = await monitor_stage.wait_for_resource()

        etcd_stage = EtcdStage(EtcdProvisioner())
        etcd_spec = EtcdSpec(local_config=local_config)
        await etcd_stage.setup(EtcdSpecGenerator(etcd_spec))
        etcd_result = await etcd_stage.wait_for_resource()

        redis_config_stage = RedisConfigStage(RedisConfigProvisioner())
        redis_config_spec = RedisConfigSpec(etcd=etcd_result.etcd)
        await redis_config_stage.setup(RedisConfigSpecGenerator(redis_config_spec))
        redis_config_result = await redis_config_stage.wait_for_resource()
        redis_profile_target = redis_config_result.redis_config.to_redis_profile_target()

        mq_stage = MessageQueueStage(MessageQueueProvisioner())
        mq_spec = MessageQueueSpec(
            local_config=local_config, redis_profile_target=redis_profile_target
        )
        await mq_stage.setup(MessageQueueSpecGenerator(mq_spec))
        mq_result = await mq_stage.wait_for_resource()

        event_dispatcher_stage = EventDispatcherStage(EventDispatcherProvisioner())
        event_dispatcher_spec = EventDispatcherSpec(
            message_queue=mq_result.message_queue,
            log_events=local_config.debug.log_events,
            event_observer=monitor_result.metric_registry.event,
            source_id=None,
        )
        await event_dispatcher_stage.setup(EventDispatcherSpecGenerator(event_dispatcher_spec))
        event_dispatcher_result = await event_dispatcher_stage.wait_for_resource()

        valkey_client_stage = ValkeyClientStage(ValkeyClientProvisioner())
        valkey_client_spec = ValkeyClientSpec(redis_profile_target)
        await valkey_client_stage.setup(ValkeyClientSpecGenerator(valkey_client_spec))
        valkey_client_result = await valkey_client_stage.wait_for_resource()

        volume_pool_stage = VolumePoolStage(VolumePoolProvisioner())
        volume_pool_spec = VolumePoolSpec(
            local_config=local_config,
            etcd=etcd_result.etcd,
            event_dispatcher=event_dispatcher_result.event_dispatcher,
            event_producer=event_dispatcher_result.event_producer,
        )
        await volume_pool_stage.setup(VolumePoolSpecGenerator(volume_pool_spec))
        volume_pool_result = await volume_pool_stage.wait_for_resource()

        bgtask_manager_stage = BgtaskManagerStage(BgtaskManagerProvisioner())
        bgtask_manager_spec = BgtaskManagerSpec(
            volume_pool=volume_pool_result.volume_pool,
            valkey_client=valkey_client_result.bgtask_client,
            event_producer=event_dispatcher_result.event_producer,
            node_id=local_config.storage_proxy.node_id,
            tags=[PRIVILEGED_WORKER_TAG],
        )
        await bgtask_manager_stage.setup(BgtaskManagerSpecGenerator(bgtask_manager_spec))
        bgtask_manager_result = await bgtask_manager_stage.wait_for_resource()

        event_registry_stage = EventRegistryStage(EventRegistryProvisioner())
        event_registry_spec = EventRegistrySpec(
            bgtask_mgr=bgtask_manager_result.bgtask_mgr,
            event_dispatcher=event_dispatcher_result.event_dispatcher,
        )
        await event_registry_stage.setup(EventRegistrySpecGenerator(event_registry_spec))
        await event_registry_stage.wait_for_resource()

        return BootstrapResult(
            logger=logger_result,
            monitor=monitor_result,
            etcd=etcd_result,
            redis_config=redis_config_result,
            message_queue=mq_result,
            event_dispatcher=event_dispatcher_result,
            valkey_client=valkey_client_result,
            volume_pool=volume_pool_result,
            bgtask_manager=bgtask_manager_result,
        )

    @override
    async def teardown(self, resource: BootstrapResult) -> None:
        pass


class BootstrapStage(ProvisionStage[BootstrapSpec, BootstrapResult]):
    pass
