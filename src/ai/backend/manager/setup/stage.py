from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.data.config.types import EtcdConfigData
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.metrics.metric import CommonMetricRegistry
from ai.backend.common.plugin.event import EventDispatcherPluginContext
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.types import RedisProfileTarget
from ai.backend.logging import LogLevel
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.idle import IdleCheckerHost
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.repositories.repositories import Repositories
from ai.backend.manager.scheduler.dispatcher import SchedulerDispatcher
from ai.backend.manager.service.base import ServicesContext
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.setup.background.sweepers import SweeperTask
from ai.backend.manager.setup.infrastructure.redis import ValkeyClients
from ai.backend.manager.setup.services.discovery import ServiceDiscoveryResource
from ai.backend.manager.types import DistributedLockFactory

# Import all provisioners
from .background.sweepers import (
    StaleKernelSweeperProvisioner,
    StaleKernelSweeperSpec,
    StaleSessionSweeperProvisioner,
    StaleSessionSweeperSpec,
)
from .core.agent_registry import (
    AgentRegistryProvisioner,
    AgentRegistryResource,
    AgentRegistrySpec,
)
from .core.idle_checker import IdleCheckerProvisioner, IdleCheckerSpec
from .core.scheduler import SchedulerDispatcherProvisioner, SchedulerDispatcherSpec
from .highlevel.background_tasks import (
    BackgroundTaskManagerProvisioner,
    BackgroundTaskManagerSpec,
)
from .highlevel.event_dispatcher import EventDispatcherProvisioner, EventDispatcherSpec
from .highlevel.processors import ProcessorsProvisioner, ProcessorsSpec
from .infrastructure.config import ConfigProviderProvisioner, ConfigProviderSpec
from .infrastructure.database import DatabaseProvisioner, DatabaseSpec
from .infrastructure.etcd import EtcdProvisioner, EtcdSpec
from .infrastructure.event_hub import EventHubProvisioner, EventHubSpec
from .infrastructure.redis import ValkeyClientsProvisioner, ValkeyClientsSpec
from .infrastructure.storage import StorageManagerProvisioner, StorageManagerSpec
from .messaging.distributed_lock import DistributedLockProvisioner, DistributedLockSpec
from .messaging.event_producer import (
    EventProducerProvisioner,
    EventProducerResource,
    EventProducerSpec,
)
from .messaging.message_queue import MessageQueueProvisioner, MessageQueueSpec
from .plugins.event_dispatcher import (
    EventDispatcherPluginProvisioner,
    EventDispatcherPluginSpec,
)
from .plugins.hook import HookPluginProvisioner, HookPluginSpec
from .plugins.monitoring import (
    MonitoringContext,
    MonitoringProvisioner,
    MonitoringSpec,
)
from .plugins.network import NetworkPluginProvisioner, NetworkPluginSpec
from .services.discovery import ServiceDiscoveryProvisioner, ServiceDiscoverySpec
from .services.repositories import RepositoriesProvisioner, RepositoriesSpec
from .services.services import ServicesProvisioner, ServicesSpec


@dataclass
class ManagerSetupSpec:
    """Initial configuration values for Manager setup"""

    config_path: Optional[Path]
    log_level: LogLevel
    etcd_config: EtcdConfigData
    debug: bool = False
    extra_config: Optional[dict] = None

    # External dependencies injected from outside
    metrics: CommonMetricRegistry = field(default_factory=CommonMetricRegistry.instance)


@dataclass
class ManagerSetupResult:
    """Container for all provisioned resources"""

    # Phase 1: Core Infrastructure
    etcd: AsyncEtcd
    event_hub: EventHub

    # Phase 2: Configuration
    config_provider: ManagerConfigProvider

    # Phase 3: Data Storage
    valkey_clients: ValkeyClients
    database: ExtendedAsyncSAEngine
    storage_manager: StorageSessionManager

    # Phase 4: Messaging and Events
    message_queue: AbstractMessageQueue
    event_producer_resource: EventProducerResource
    distributed_lock_factory: DistributedLockFactory

    # Phase 5: Plugin Systems
    hook_plugin_ctx: HookPluginContext
    network_plugin_ctx: NetworkPluginContext
    event_dispatcher_plugin_ctx: EventDispatcherPluginContext
    monitoring_context: MonitoringContext

    # Phase 6: Service Layer
    repositories: Repositories
    services_ctx: ServicesContext
    service_discovery_resource: ServiceDiscoveryResource

    # Phase 7: Core Manager Components
    agent_registry_resource: AgentRegistryResource
    idle_checker_host: IdleCheckerHost
    scheduler_dispatcher: SchedulerDispatcher

    # Phase 8: High-Level Components
    event_dispatcher: EventDispatcher
    background_task_manager: BackgroundTaskManager
    processors: Processors

    # Phase 9: Background Services
    stale_session_sweeper: SweeperTask
    stale_kernel_sweeper: SweeperTask

    # Metrics from spec
    metrics: CommonMetricRegistry

    def to_root_context(self) -> dict:
        """Convert to RootContext-compatible dictionary for backward compatibility"""
        return {
            # Direct mappings
            "etcd": self.etcd,
            "event_hub": self.event_hub,
            "config_provider": self.config_provider,
            "db": self.database,
            "storage_manager": self.storage_manager,
            "message_queue": self.message_queue,
            "event_producer": self.event_producer_resource.event_producer,
            "event_fetcher": self.event_producer_resource.event_fetcher,
            "distributed_lock_factory": self.distributed_lock_factory,
            "hook_plugin_ctx": self.hook_plugin_ctx,
            "network_plugin_ctx": self.network_plugin_ctx,
            "event_dispatcher_plugin_ctx": self.event_dispatcher_plugin_ctx,
            "error_monitor": self.monitoring_context.error_monitor,
            "stats_monitor": self.monitoring_context.stats_monitor,
            "repositories": self.repositories,
            "services_ctx": self.services_ctx,
            "registry": self.agent_registry_resource.registry,
            "agent_cache": self.agent_registry_resource.agent_cache,
            "idle_checker_host": self.idle_checker_host,
            "scheduler_dispatcher": self.scheduler_dispatcher,
            "event_dispatcher": self.event_dispatcher,
            "background_task_manager": self.background_task_manager,
            "processors": self.processors,
            "metrics": self.metrics,
            # Valkey clients
            "valkey_live": self.valkey_clients.valkey_live,
            "valkey_stat": self.valkey_clients.valkey_stat,
            "valkey_image": self.valkey_clients.valkey_image,
            "valkey_stream": self.valkey_clients.valkey_stream,
            # Service discovery
            "service_discovery": self.service_discovery_resource.service_discovery,
            "sd_loop": self.service_discovery_resource.sd_loop,
        }


class ManagerSetupStage:
    """Main stage that orchestrates all provisioners with manual dependency management"""

    def __init__(self):
        # Initialize all provisioners
        self.etcd_provisioner = EtcdProvisioner()
        self.event_hub_provisioner = EventHubProvisioner()
        self.config_provider_provisioner = ConfigProviderProvisioner()
        self.valkey_clients_provisioner = ValkeyClientsProvisioner()
        self.database_provisioner = DatabaseProvisioner()
        self.storage_manager_provisioner = StorageManagerProvisioner()
        self.message_queue_provisioner = MessageQueueProvisioner()
        self.event_producer_provisioner = EventProducerProvisioner()
        self.distributed_lock_provisioner = DistributedLockProvisioner()
        self.hook_plugin_provisioner = HookPluginProvisioner()
        self.network_plugin_provisioner = NetworkPluginProvisioner()
        self.event_dispatcher_plugin_provisioner = EventDispatcherPluginProvisioner()
        self.monitoring_provisioner = MonitoringProvisioner()
        self.repositories_provisioner = RepositoriesProvisioner()
        self.services_provisioner = ServicesProvisioner()
        self.service_discovery_provisioner = ServiceDiscoveryProvisioner()
        self.agent_registry_provisioner = AgentRegistryProvisioner()
        self.idle_checker_provisioner = IdleCheckerProvisioner()
        self.scheduler_dispatcher_provisioner = SchedulerDispatcherProvisioner()
        self.event_dispatcher_provisioner = EventDispatcherProvisioner()
        self.background_task_manager_provisioner = BackgroundTaskManagerProvisioner()
        self.processors_provisioner = ProcessorsProvisioner()
        self.stale_session_sweeper_provisioner = StaleSessionSweeperProvisioner()
        self.stale_kernel_sweeper_provisioner = StaleKernelSweeperProvisioner()

    async def run(self, spec: ManagerSetupSpec) -> ManagerSetupResult:
        """Execute all provisioners in dependency order"""

        # Phase 1: Core Infrastructure (no dependencies)
        etcd = await self.etcd_provisioner.setup(EtcdSpec(config=spec.etcd_config))
        event_hub = await self.event_hub_provisioner.setup(EventHubSpec())

        # Phase 2: Configuration (depends on etcd)
        config_provider = await self.config_provider_provisioner.setup(
            ConfigProviderSpec(
                etcd=etcd,
                log_level=spec.log_level,
                config_path=spec.config_path,
                extra_config=spec.extra_config,
                debug=spec.debug,
            )
        )

        # Phase 3: Data Storage (depends on config_provider)
        valkey_clients = await self.valkey_clients_provisioner.setup(
            ValkeyClientsSpec(config=config_provider.config)
        )
        database = await self.database_provisioner.setup(
            DatabaseSpec(config=config_provider.config)
        )
        storage_manager = await self.storage_manager_provisioner.setup(
            StorageManagerSpec(config=config_provider.config)
        )

        # Phase 4: Messaging and Events
        message_queue = await self.message_queue_provisioner.setup(
            MessageQueueSpec(config=config_provider.config)
        )
        event_producer_resource = await self.event_producer_provisioner.setup(
            EventProducerSpec(
                config=config_provider.config,
                message_queue=message_queue,
            )
        )
        distributed_lock_factory = await self.distributed_lock_provisioner.setup(
            DistributedLockSpec(
                config=config_provider.config,
                etcd=etcd,
                database=database,
            )
        )

        # Phase 5: Plugin Systems
        hook_plugin_ctx = await self.hook_plugin_provisioner.setup(
            HookPluginSpec(config=config_provider.config, etcd=etcd)
        )
        network_plugin_ctx = await self.network_plugin_provisioner.setup(
            NetworkPluginSpec(config=config_provider.config, etcd=etcd)
        )
        event_dispatcher_plugin_ctx = await self.event_dispatcher_plugin_provisioner.setup(
            EventDispatcherPluginSpec(config=config_provider.config, etcd=etcd)
        )
        monitoring_context = await self.monitoring_provisioner.setup(
            MonitoringSpec(config=config_provider.config, etcd=etcd)
        )

        # Phase 6: Service Layer
        repositories = await self.repositories_provisioner.setup(
            RepositoriesSpec(
                database=database,
                storage_manager=storage_manager,
                config_provider=config_provider,
                valkey_clients=valkey_clients,
            )
        )
        services_ctx = await self.services_provisioner.setup(ServicesSpec(database=database))
        # Create redis_profile_target from config
        redis_profile_target = RedisProfileTarget.from_dict(
            config_provider.config.redis.model_dump()
        )

        service_discovery_resource = await self.service_discovery_provisioner.setup(
            ServiceDiscoverySpec(
                config=config_provider.config,
                etcd=etcd,
                redis_profile_target=redis_profile_target,
            )
        )

        # Phase 7: Core Manager Components
        agent_registry_resource = await self.agent_registry_provisioner.setup(
            AgentRegistrySpec(
                config_provider=config_provider,
                database=database,
                valkey_clients=valkey_clients,
                event_producer_resource=event_producer_resource,
                storage_manager=storage_manager,
                hook_plugin_ctx=hook_plugin_ctx,
                network_plugin_ctx=network_plugin_ctx,
            )
        )
        idle_checker_host = await self.idle_checker_provisioner.setup(
            IdleCheckerSpec(
                database=database,
                config_provider=config_provider,
                event_producer_resource=event_producer_resource,
                distributed_lock_factory=distributed_lock_factory,
            )
        )
        scheduler_dispatcher = await self.scheduler_dispatcher_provisioner.setup(
            SchedulerDispatcherSpec(
                config_provider=config_provider,
                etcd=etcd,
                event_producer_resource=event_producer_resource,
                distributed_lock_factory=distributed_lock_factory,
                agent_registry_resource=agent_registry_resource,
                valkey_clients=valkey_clients,
                repositories=repositories,
            )
        )

        # Phase 8: High-Level Components
        event_dispatcher = await self.event_dispatcher_provisioner.setup(
            EventDispatcherSpec(
                config=config_provider.config,
                message_queue=message_queue,
                valkey_clients=valkey_clients,
                scheduler_dispatcher=scheduler_dispatcher,
                event_hub=event_hub,
                agent_registry_resource=agent_registry_resource,
                database=database,
                idle_checker_host=idle_checker_host,
                event_dispatcher_plugin_ctx=event_dispatcher_plugin_ctx,
                event_observer=spec.metrics.event,
            )
        )
        background_task_manager = await self.background_task_manager_provisioner.setup(
            BackgroundTaskManagerSpec(
                event_producer_resource=event_producer_resource,
                bgtask_observer=spec.metrics.bgtask,
            )
        )
        processors = await self.processors_provisioner.setup(
            ProcessorsSpec(
                config=config_provider.config,
                database=database,
                repositories=repositories,
                etcd=etcd,
                config_provider=config_provider,
                storage_manager=storage_manager,
                valkey_clients=valkey_clients,
                event_producer_resource=event_producer_resource,
                background_task_manager=background_task_manager,
                event_hub=event_hub,
                agent_registry_resource=agent_registry_resource,
                monitoring_context=monitoring_context,
                idle_checker_host=idle_checker_host,
                event_dispatcher=event_dispatcher,
                hook_plugin_ctx=hook_plugin_ctx,
            )
        )

        # Phase 9: Background Services
        stale_session_sweeper = await self.stale_session_sweeper_provisioner.setup(
            StaleSessionSweeperSpec(
                etcd=etcd,
                database=database,
                agent_registry_resource=agent_registry_resource,
                sweeper_metric=spec.metrics.sweeper,
            )
        )
        stale_kernel_sweeper = await self.stale_kernel_sweeper_provisioner.setup(
            StaleKernelSweeperSpec(
                etcd=etcd,
                database=database,
                agent_registry_resource=agent_registry_resource,
                sweeper_metric=spec.metrics.sweeper,
            )
        )

        return ManagerSetupResult(
            # Phase 1
            etcd=etcd,
            event_hub=event_hub,
            # Phase 2
            config_provider=config_provider,
            # Phase 3
            valkey_clients=valkey_clients,
            database=database,
            storage_manager=storage_manager,
            # Phase 4
            message_queue=message_queue,
            event_producer_resource=event_producer_resource,
            distributed_lock_factory=distributed_lock_factory,
            # Phase 5
            hook_plugin_ctx=hook_plugin_ctx,
            network_plugin_ctx=network_plugin_ctx,
            event_dispatcher_plugin_ctx=event_dispatcher_plugin_ctx,
            monitoring_context=monitoring_context,
            # Phase 6
            repositories=repositories,
            services_ctx=services_ctx,
            service_discovery_resource=service_discovery_resource,
            # Phase 7
            agent_registry_resource=agent_registry_resource,
            idle_checker_host=idle_checker_host,
            scheduler_dispatcher=scheduler_dispatcher,
            # Phase 8
            event_dispatcher=event_dispatcher,
            background_task_manager=background_task_manager,
            processors=processors,
            # Phase 9
            stale_session_sweeper=stale_session_sweeper,
            stale_kernel_sweeper=stale_kernel_sweeper,
            # Metrics
            metrics=spec.metrics,
        )

    async def teardown(self, result: ManagerSetupResult) -> None:
        """Teardown all resources in reverse order"""
        # Phase 9: Background Services
        await self.stale_kernel_sweeper_provisioner.teardown(result.stale_kernel_sweeper)
        await self.stale_session_sweeper_provisioner.teardown(result.stale_session_sweeper)

        # Phase 8: High-Level Components
        await self.processors_provisioner.teardown(result.processors)
        await self.background_task_manager_provisioner.teardown(result.background_task_manager)
        await self.event_dispatcher_provisioner.teardown(result.event_dispatcher)

        # Phase 7: Core Manager Components
        await self.scheduler_dispatcher_provisioner.teardown(result.scheduler_dispatcher)
        await self.idle_checker_provisioner.teardown(result.idle_checker_host)
        await self.agent_registry_provisioner.teardown(result.agent_registry_resource)

        # Phase 6: Service Layer
        await self.service_discovery_provisioner.teardown(result.service_discovery_resource)
        await self.services_provisioner.teardown(result.services_ctx)
        await self.repositories_provisioner.teardown(result.repositories)

        # Phase 5: Plugin Systems
        await self.monitoring_provisioner.teardown(result.monitoring_context)
        await self.event_dispatcher_plugin_provisioner.teardown(result.event_dispatcher_plugin_ctx)
        await self.network_plugin_provisioner.teardown(result.network_plugin_ctx)
        await self.hook_plugin_provisioner.teardown(result.hook_plugin_ctx)

        # Phase 4: Messaging and Events
        await self.distributed_lock_provisioner.teardown(result.distributed_lock_factory)
        await self.event_producer_provisioner.teardown(result.event_producer_resource)
        await self.message_queue_provisioner.teardown(result.message_queue)

        # Phase 3: Data Storage
        await self.storage_manager_provisioner.teardown(result.storage_manager)
        await self.database_provisioner.teardown(result.database)
        await self.valkey_clients_provisioner.teardown(result.valkey_clients)

        # Phase 2: Configuration
        await self.config_provider_provisioner.teardown(result.config_provider)

        # Phase 1: Core Infrastructure
        await self.event_hub_provisioner.teardown(result.event_hub)
        await self.etcd_provisioner.teardown(result.etcd)
