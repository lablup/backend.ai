from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.clients.prometheus.client import PrometheusClient
from ai.backend.common.clients.valkey_client.valkey_artifact.client import (
    ValkeyArtifactDownloadTrackingClient,
)
from ai.backend.common.clients.valkey_client.valkey_container_log.client import (
    ValkeyContainerLogClient,
)
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.clients.valkey_client.valkey_stream.client import ValkeyStreamClient
from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventObserver, EventProducer
from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.message_queue.abc.queue import AbstractMessageQueue
from ai.backend.common.plugin.event import EventDispatcherPluginContext
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.plugin.monitor import ErrorPluginContext
from ai.backend.manager.actions.monitors.audit_log import AuditLogMonitor
from ai.backend.manager.actions.monitors.prometheus import PrometheusMonitor
from ai.backend.manager.actions.monitors.reporter import ReporterMonitor
from ai.backend.manager.agent_cache import AgentRPCCache
from ai.backend.manager.clients.agent.pool import AgentClientPool
from ai.backend.manager.clients.appproxy.client import AppProxyClientPool
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.event_dispatcher.dispatch import DispatcherArgs, Dispatchers
from ai.backend.manager.idle import IdleCheckerHost
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.notification import NotificationCenter
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.reporters.base import AbstractReporter
from ai.backend.manager.reporters.hub import ReporterHub, ReporterHubArgs
from ai.backend.manager.reporters.smtp import SMTPReporter, SMTPSenderArgs
from ai.backend.manager.repositories.repositories import Repositories
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.services.processors import Processors, ServiceArgs
from ai.backend.manager.sokovan.deployment import DeploymentController
from ai.backend.manager.sokovan.deployment.coordinator import DeploymentCoordinator
from ai.backend.manager.sokovan.deployment.revision_generator.registry import (
    RevisionGeneratorRegistry,
)
from ai.backend.manager.sokovan.deployment.route.coordinator import RouteCoordinator
from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from ai.backend.manager.types import SMTPTriggerPolicy

from .bgtask_registry import BgtaskRegistryDependency, BgtaskRegistryInput
from .event_dispatcher import EventDispatcherDependency, EventDispatcherInput
from .processors import ProcessorsDependency, ProcessorsProviderInput


@dataclass
class ProcessingInput:
    """Input required for processing layer setup.

    Contains all dependencies needed for event dispatcher,
    processors, and background task registry.
    """

    # EventDispatcher creation
    message_queue: AbstractMessageQueue
    log_events: bool
    event_observer: EventObserver | None

    # Dispatchers registration (DispatcherArgs)
    valkey_container_log: ValkeyContainerLogClient
    valkey_stat: ValkeyStatClient
    valkey_stream: ValkeyStreamClient
    schedule_coordinator: ScheduleCoordinator
    scheduling_controller: SchedulingController
    deployment_coordinator: DeploymentCoordinator
    route_coordinator: RouteCoordinator
    scheduler_repository: SchedulerRepository
    event_hub: EventHub
    agent_registry: AgentRegistry
    db: ExtendedAsyncSAEngine
    idle_checker_host: IdleCheckerHost
    event_dispatcher_plugin_ctx: EventDispatcherPluginContext
    repositories: Repositories
    storage_manager: StorageSessionManager
    config_provider: ManagerConfigProvider
    event_producer: EventProducer

    # Processors creation (ServiceArgs additional)
    etcd: AsyncEtcd
    valkey_live: ValkeyLiveClient
    valkey_artifact_client: ValkeyArtifactDownloadTrackingClient
    event_fetcher: EventFetcher
    background_task_manager: BackgroundTaskManager
    error_monitor: ErrorPluginContext
    hook_plugin_ctx: HookPluginContext
    deployment_controller: DeploymentController
    revision_generator_registry: RevisionGeneratorRegistry
    agent_cache: AgentRPCCache
    notification_center: NotificationCenter
    appproxy_client_pool: AppProxyClientPool
    prometheus_client: PrometheusClient

    # BgtaskRegistry creation (additional)
    agent_client_pool: AgentClientPool


@dataclass
class ProcessingResources:
    """Container for processing layer resources."""

    event_dispatcher: EventDispatcher
    processors: Processors


def _make_registered_reporters(
    config_provider: ManagerConfigProvider,
) -> dict[str, AbstractReporter]:
    reporters: dict[str, AbstractReporter] = {}
    smtp_configs = config_provider.config.reporter.smtp
    for smtp_conf in smtp_configs:
        smtp_args = SMTPSenderArgs(
            host=smtp_conf.host,
            port=smtp_conf.port,
            username=smtp_conf.username,
            password=smtp_conf.password,
            sender=smtp_conf.sender,
            recipients=smtp_conf.recipients,
            use_tls=smtp_conf.use_tls,
            max_workers=smtp_conf.max_workers,
            template=smtp_conf.template,
        )
        trigger_policy = SMTPTriggerPolicy[smtp_conf.trigger_policy]
        reporters[smtp_conf.name] = SMTPReporter(smtp_args, trigger_policy)
    return reporters


def _make_action_reporters(
    config_provider: ManagerConfigProvider,
    reporters: dict[str, AbstractReporter],
) -> dict[str, list[AbstractReporter]]:
    action_monitors: dict[str, list[AbstractReporter]] = {}
    action_monitor_configs = config_provider.config.reporter.action_monitors
    for action_monitor_conf in action_monitor_configs:
        reporter_name: str = action_monitor_conf.reporter
        reporter = reporters.get(reporter_name)
        if reporter is None:
            continue
        for action_type in action_monitor_conf.subscribed_actions:
            action_monitors.setdefault(action_type, []).append(reporter)
    return action_monitors


class ProcessingComposer(DependencyComposer[ProcessingInput, ProcessingResources]):
    """Composes event dispatcher, processors, and background task registry.

    Orchestrates the processing layer (Layer 6-7) initialization:
    1. EventDispatcher: Created first (not yet started)
    2. Processors: Created with event_dispatcher reference
    3. Dispatchers: Registered on event_dispatcher, then started
    4. BgtaskRegistry: Created and set on background_task_manager
    """

    @property
    def stage_name(self) -> str:
        return "processing"

    @asynccontextmanager
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: ProcessingInput,
    ) -> AsyncIterator[ProcessingResources]:
        # Step 1: Create EventDispatcher (not started yet)
        event_dispatcher = await stack.enter_dependency(
            EventDispatcherDependency(),
            EventDispatcherInput(
                message_queue=setup_input.message_queue,
                log_events=setup_input.log_events,
                event_observer=setup_input.event_observer,
            ),
        )

        # Step 2: Build action monitors and create Processors
        registered_reporters = _make_registered_reporters(setup_input.config_provider)
        action_reporters = _make_action_reporters(setup_input.config_provider, registered_reporters)
        reporter_hub = ReporterHub(ReporterHubArgs(reporters=action_reporters))
        reporter_monitor = ReporterMonitor(reporter_hub)
        prometheus_monitor = PrometheusMonitor()
        audit_log_monitor = AuditLogMonitor(setup_input.repositories.audit_log.repository)

        service_args = ServiceArgs(
            db=setup_input.db,
            repositories=setup_input.repositories,
            etcd=setup_input.etcd,
            config_provider=setup_input.config_provider,
            storage_manager=setup_input.storage_manager,
            valkey_stat_client=setup_input.valkey_stat,
            valkey_live=setup_input.valkey_live,
            valkey_artifact_client=setup_input.valkey_artifact_client,
            event_fetcher=setup_input.event_fetcher,
            background_task_manager=setup_input.background_task_manager,
            event_hub=setup_input.event_hub,
            agent_registry=setup_input.agent_registry,
            error_monitor=setup_input.error_monitor,
            idle_checker_host=setup_input.idle_checker_host,
            event_dispatcher=event_dispatcher,
            hook_plugin_ctx=setup_input.hook_plugin_ctx,
            scheduling_controller=setup_input.scheduling_controller,
            deployment_controller=setup_input.deployment_controller,
            revision_generator_registry=setup_input.revision_generator_registry,
            event_producer=setup_input.event_producer,
            agent_cache=setup_input.agent_cache,
            notification_center=setup_input.notification_center,
            appproxy_client_pool=setup_input.appproxy_client_pool,
            prometheus_client=setup_input.prometheus_client,
        )

        processors = await stack.enter_dependency(
            ProcessorsDependency(),
            ProcessorsProviderInput(
                service_args=service_args,
                action_monitors=[reporter_monitor, prometheus_monitor, audit_log_monitor],
            ),
        )

        # Step 3: Register Dispatchers and start EventDispatcher
        dispatchers = Dispatchers(
            DispatcherArgs(
                valkey_container_log=setup_input.valkey_container_log,
                valkey_stat=setup_input.valkey_stat,
                valkey_stream=setup_input.valkey_stream,
                schedule_coordinator=setup_input.schedule_coordinator,
                scheduling_controller=setup_input.scheduling_controller,
                deployment_coordinator=setup_input.deployment_coordinator,
                route_coordinator=setup_input.route_coordinator,
                scheduler_repository=setup_input.scheduler_repository,
                event_hub=setup_input.event_hub,
                agent_registry=setup_input.agent_registry,
                db=setup_input.db,
                idle_checker_host=setup_input.idle_checker_host,
                event_dispatcher_plugin_ctx=setup_input.event_dispatcher_plugin_ctx,
                repositories=setup_input.repositories,
                processors_factory=lambda: processors,
                storage_manager=setup_input.storage_manager,
                config_provider=setup_input.config_provider,
                event_producer=setup_input.event_producer,
            )
        )
        dispatchers.dispatch(event_dispatcher)
        await event_dispatcher.start()

        # Step 4: Create BgtaskRegistry
        await stack.enter_dependency(
            BgtaskRegistryDependency(),
            BgtaskRegistryInput(
                processors=processors,
                background_task_manager=setup_input.background_task_manager,
                repositories=setup_input.repositories,
                agent_client_pool=setup_input.agent_client_pool,
                agent_registry=setup_input.agent_registry,
                event_hub=setup_input.event_hub,
                event_fetcher=setup_input.event_fetcher,
            ),
        )

        yield ProcessingResources(
            event_dispatcher=event_dispatcher,
            processors=processors,
        )
