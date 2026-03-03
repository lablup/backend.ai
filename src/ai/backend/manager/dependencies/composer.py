from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.logging.types import LogLevel
from ai.backend.manager.plugin.monitor import ManagerErrorPluginContext, ManagerStatsPluginContext

from .agents import AgentsComposer, AgentsInput, AgentsResources
from .bootstrap import BootstrapComposer, BootstrapInput, BootstrapResources
from .components import ComponentsComposer, ComponentsInput, ComponentsResources
from .domain import DomainComposer, DomainInput, DomainResources
from .errors import DependencyInitializationError
from .infrastructure import (
    InfrastructureComposer,
    InfrastructureInput,
    InfrastructureResources,
)
from .messaging import MessagingComposer, MessagingInput, MessagingResources
from .orchestration import OrchestrationComposer, OrchestrationInput, OrchestrationResources
from .plugins import PluginsComposer, PluginsResources
from .plugins.base import PluginsInput
from .plugins.monitoring import ErrorMonitorDependency, MonitoringInput, StatsMonitorDependency
from .processing import ProcessingComposer, ProcessingInput, ProcessingResources
from .system import SystemComposer, SystemInput, SystemResources


@dataclass
class DependencyInput:
    """Input required for complete dependency setup.

    Contains only the essential parameters: config file path, log level,
    and process index.
    """

    config_path: Path
    pidx: int = 0
    log_level: LogLevel = LogLevel.NOTSET


@dataclass
class MonitoringResources:
    """Container for monitoring plugin resources.

    Initialized after DomainComposer so that error_log_repository is available.
    """

    error_monitor: ManagerErrorPluginContext | None
    stats_monitor: ManagerStatsPluginContext | None


@dataclass
class DependencyResources:
    """Container for all initialized dependency resources.

    Holds all dependencies in the correct initialization order:
    0. Bootstrap stage: etcd, config provider
    1. Infrastructure stage: valkey clients, database
    2. Components stage: storage manager, agent cache
    3. Plugins stage: hook, network, event dispatcher plugin contexts
    4. Messaging stage: event hub, message queue, event producer, event fetcher
    5. Domain stage: notification center, distributed lock, repositories, services
    6. Monitoring stage: error_monitor, stats_monitor (requires Domain repositories)
    7. System stage: CORS, metrics, GQL adapter, JWT, prometheus, service discovery
    8. Agents stage: controllers, client pools, agent registry
    9. Orchestration stage: idle checker, sokovan, leader election
    10. Processing stage: event dispatcher, processors
    """

    bootstrap: BootstrapResources
    infrastructure: InfrastructureResources
    components: ComponentsResources
    plugins: PluginsResources
    messaging: MessagingResources
    domain: DomainResources
    monitoring: MonitoringResources
    system: SystemResources
    agents: AgentsResources
    orchestration: OrchestrationResources
    processing: ProcessingResources


class ManagerDependencyComposer(DependencyComposer[DependencyInput, DependencyResources]):
    """Composes all manager dependencies in the correct order.

    Composes the full dependency initialization across 10 stages:
    1. Bootstrap: etcd and config provider
    2. Infrastructure: valkey clients and database
    3. Components: storage manager and agent cache
    4. Plugins: hook, network, event dispatcher plugin contexts
    5. Messaging: event hub, message queue, event producer, event fetcher
    6. Domain: notification center, distributed lock, repositories, services
    7. System: CORS, metrics, GQL, JWT, prometheus, service discovery, bgtask mgr
    8. Agents: scheduling/deployment/route controllers, client pools, registry
    9. Orchestration: idle checker, sokovan orchestrator, leader election
    10. Processing: event dispatcher, processors, bgtask registry
    """

    @property
    def stage_name(self) -> str:
        return "manager-dependencies"

    @asynccontextmanager
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: DependencyInput,
    ) -> AsyncIterator[DependencyResources]:
        """Compose all dependencies in order using the provided stack.

        Args:
            stack: The dependency stack to use for composition
            setup_input: Dependency input containing config path, pidx, and log level

        Yields:
            DependencyResources containing all initialized resources
        """
        # Stage 1: Bootstrap (etcd + config provider)
        bootstrap = await stack.enter_composer(
            BootstrapComposer(),
            BootstrapInput(
                config_path=setup_input.config_path,
                log_level=setup_input.log_level,
            ),
        )
        config = bootstrap.config_provider.config

        # Stage 2: Infrastructure (valkey + database)
        infrastructure = await stack.enter_composer(
            InfrastructureComposer(),
            InfrastructureInput(
                config=config,
                etcd=bootstrap.etcd,
            ),
        )

        # Stage 3: Components (storage manager + agent cache)
        components = await stack.enter_composer(
            ComponentsComposer(),
            ComponentsInput(
                config=config,
                db=infrastructure.db,
                etcd=bootstrap.etcd,
            ),
        )

        # Stage 4: Plugins (hook, network, event dispatcher plugin contexts)
        plugins = await stack.enter_composer(
            PluginsComposer(),
            PluginsInput(
                etcd=bootstrap.etcd,
                local_config=config.model_dump(by_alias=True),
                allowed_plugins=config.manager.allowed_plugins,
                disabled_plugins=config.manager.disabled_plugins,
            ),
        )

        # Stage 5: Messaging (event hub, message queue, event producer, event fetcher)
        messaging = await stack.enter_composer(
            MessagingComposer(),
            MessagingInput(config=config),
        )

        # Stage 6: Domain (notification center, distributed lock, repositories, services)
        domain = await stack.enter_composer(
            DomainComposer(),
            DomainInput(
                config_provider=bootstrap.config_provider,
                db=infrastructure.db,
                etcd=bootstrap.etcd,
                storage_manager=components.storage_manager,
                valkey_stat=infrastructure.valkey.stat,
                valkey_live=infrastructure.valkey.live,
                valkey_schedule=infrastructure.valkey.schedule,
                valkey_image=infrastructure.valkey.image,
            ),
        )

        # Stage 6.5: Monitoring (error_monitor, stats_monitor)
        # Must run after Domain so that error_log_repository is available.
        monitoring_input = MonitoringInput(
            etcd=bootstrap.etcd,
            local_config=config.model_dump(by_alias=True),
            allowed_plugins=config.manager.allowed_plugins,
            disabled_plugins=config.manager.disabled_plugins,
            error_log_repository=domain.repositories.error_log.repository,
        )
        error_monitor = await stack.enter_dependency(
            ErrorMonitorDependency(),
            monitoring_input,
        )
        stats_monitor = await stack.enter_dependency(
            StatsMonitorDependency(),
            monitoring_input,
        )
        monitoring = MonitoringResources(
            error_monitor=error_monitor,
            stats_monitor=stats_monitor,
        )

        # Stage 7: System (CORS, metrics, GQL, JWT, prometheus, service discovery, bgtask mgr)
        system = await stack.enter_composer(
            SystemComposer(),
            SystemInput(
                config=config,
                etcd=bootstrap.etcd,
                valkey=infrastructure.valkey,
                db=infrastructure.db,
                event_producer=messaging.event_producer,
                valkey_profile_target=config.redis.to_valkey_profile_target(),
            ),
        )

        # Stage 8: Agents (controllers, client pools, agent registry)
        agents = await stack.enter_composer(
            AgentsComposer(),
            AgentsInput(
                config=config,
                config_provider=bootstrap.config_provider,
                db=infrastructure.db,
                valkey_clients=infrastructure.valkey,
                storage_manager=components.storage_manager,
                agent_cache=components.agent_cache,
                event_producer=messaging.event_producer,
                event_hub=messaging.event_hub,
                hook_plugin_ctx=plugins.hook_plugin_ctx,
                network_plugin_ctx=plugins.network_plugin_ctx,
                scheduler_repository=domain.repositories.scheduler.repository,
                deployment_repository=domain.repositories.deployment.repository,
            ),
        )

        # Stage 9: Orchestration (idle checker, sokovan orchestrator, leader election)
        orchestration = await stack.enter_composer(
            OrchestrationComposer(),
            OrchestrationInput(
                db=infrastructure.db,
                config_provider=bootstrap.config_provider,
                event_producer=messaging.event_producer,
                distributed_lock_factory=domain.distributed_lock_factory,
                valkey_profile_target=config.redis.to_valkey_profile_target(),
                valkey_schedule=infrastructure.valkey.schedule,
                valkey_stat=infrastructure.valkey.stat,
                pidx=setup_input.pidx,
                scheduler_repository=domain.repositories.scheduler.repository,
                deployment_repository=domain.repositories.deployment.repository,
                fair_share_repository=domain.repositories.fair_share.repository,
                resource_usage_repository=domain.repositories.resource_usage_history.repository,
                agent_client_pool=agents.agent_client_pool,
                network_plugin_ctx=plugins.network_plugin_ctx,
                scheduling_controller=agents.scheduling_controller,
                deployment_controller=agents.deployment_controller,
                route_controller=agents.route_controller,
                service_discovery=system.service_discovery,
            ),
        )

        # Stage 10: Processing (event dispatcher, processors, bgtask registry)
        # error_monitor is required by ProcessingInput; raise if not initialized
        # since the processing stage cannot function without it.
        if monitoring.error_monitor is None:
            raise DependencyInitializationError("error_monitor plugin failed to initialize")
        processing = await stack.enter_composer(
            ProcessingComposer(),
            ProcessingInput(
                # EventDispatcher creation
                message_queue=messaging.message_queue,
                log_events=config.debug.log_events,
                event_observer=system.metrics.event,
                # Dispatchers registration
                valkey_container_log=infrastructure.valkey.container_log,
                valkey_stat=infrastructure.valkey.stat,
                valkey_stream=infrastructure.valkey.stream,
                schedule_coordinator=orchestration.sokovan_orchestrator.coordinator,
                scheduling_controller=agents.scheduling_controller,
                deployment_coordinator=orchestration.sokovan_orchestrator.deployment_coordinator,
                route_coordinator=orchestration.sokovan_orchestrator.route_coordinator,
                scheduler_repository=domain.repositories.scheduler.repository,
                event_hub=messaging.event_hub,
                agent_registry=agents.registry,
                db=infrastructure.db,
                idle_checker_host=orchestration.idle_checker_host,
                event_dispatcher_plugin_ctx=plugins.event_dispatcher_plugin_ctx,
                repositories=domain.repositories,
                storage_manager=components.storage_manager,
                config_provider=bootstrap.config_provider,
                event_producer=messaging.event_producer,
                # Processors creation
                etcd=bootstrap.etcd,
                valkey_live=infrastructure.valkey.live,
                valkey_artifact_client=infrastructure.valkey.artifact,
                event_fetcher=messaging.event_fetcher,
                background_task_manager=system.background_task_manager,
                error_monitor=monitoring.error_monitor,
                hook_plugin_ctx=plugins.hook_plugin_ctx,
                deployment_controller=agents.deployment_controller,
                revision_generator_registry=agents.revision_generator_registry,
                agent_cache=components.agent_cache,
                notification_center=domain.notification_center,
                appproxy_client_pool=agents.appproxy_client_pool,
                prometheus_client=system.prometheus_client,
                # Registry quota service
                registry_quota_service=domain.services_ctx.per_project_container_registries_quota,
                # BgtaskRegistry creation
                agent_client_pool=agents.agent_client_pool,
                # Log cleanup timer
                distributed_lock_factory=domain.distributed_lock_factory,
            ),
        )

        yield DependencyResources(
            bootstrap=bootstrap,
            infrastructure=infrastructure,
            components=components,
            plugins=plugins,
            messaging=messaging,
            domain=domain,
            monitoring=monitoring,
            system=system,
            agents=agents,
            orchestration=orchestration,
            processing=processing,
        )
