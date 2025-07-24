from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.stage.types import Provisioner
from ai.backend.manager.actions.monitors.audit_log import AuditLogMonitor
from ai.backend.manager.actions.monitors.prometheus import PrometheusMonitor
from ai.backend.manager.actions.monitors.reporter import ReporterMonitor
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.idle import IdleCheckerHost
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.reporters.base import AbstractReporter
from ai.backend.manager.reporters.hub import ReporterHub, ReporterHubArgs
from ai.backend.manager.reporters.smtp import SMTPReporter, SMTPSenderArgs
from ai.backend.manager.repositories.repositories import Repositories
from ai.backend.manager.services.processors import ProcessorArgs, Processors, ServiceArgs
from ai.backend.manager.setup.core.agent_registry import AgentRegistryResource
from ai.backend.manager.setup.infrastructure.redis import ValkeyClients
from ai.backend.manager.setup.messaging.event_producer import EventProducerResource
from ai.backend.manager.setup.plugins.monitoring import MonitoringContext
from ai.backend.manager.types import SMTPTriggerPolicy


@dataclass
class ProcessorsSpec:
    config: ManagerUnifiedConfig
    database: ExtendedAsyncSAEngine
    repositories: Repositories
    etcd: AsyncEtcd
    config_provider: ManagerConfigProvider
    storage_manager: StorageSessionManager
    valkey_clients: ValkeyClients
    event_producer_resource: EventProducerResource
    background_task_manager: BackgroundTaskManager
    event_hub: EventHub
    agent_registry_resource: AgentRegistryResource
    monitoring_context: MonitoringContext
    idle_checker_host: IdleCheckerHost
    event_dispatcher: EventDispatcher
    hook_plugin_ctx: HookPluginContext


class ProcessorsProvisioner(Provisioner[ProcessorsSpec, Processors]):
    @property
    def name(self) -> str:
        return "processors"

    async def setup(self, spec: ProcessorsSpec) -> Processors:
        # Create registered reporters
        registered_reporters = self._make_registered_reporters(spec)
        action_reporters = self._make_action_reporters(spec, registered_reporters)
        
        # Create reporter hub and monitors
        reporter_hub = ReporterHub(
            ReporterHubArgs(
                reporters=action_reporters,
            )
        )
        reporter_monitor = ReporterMonitor(reporter_hub)
        prometheus_monitor = PrometheusMonitor()
        audit_log_monitor = AuditLogMonitor(spec.database)
        
        # Create processors
        processors = Processors.create(
            ProcessorArgs(
                service_args=ServiceArgs(
                    db=spec.database,
                    repositories=spec.repositories,
                    etcd=spec.etcd,
                    config_provider=spec.config_provider,
                    storage_manager=spec.storage_manager,
                    valkey_stat_client=spec.valkey_clients.valkey_stat,
                    valkey_live=spec.valkey_clients.valkey_live,
                    event_fetcher=spec.event_producer_resource.event_fetcher,
                    background_task_manager=spec.background_task_manager,
                    event_hub=spec.event_hub,
                    agent_registry=spec.agent_registry_resource.registry,
                    error_monitor=spec.monitoring_context.error_monitor,
                    idle_checker_host=spec.idle_checker_host,
                    event_dispatcher=spec.event_dispatcher,
                    hook_plugin_ctx=spec.hook_plugin_ctx,
                )
            ),
            [reporter_monitor, prometheus_monitor, audit_log_monitor],
        )
        
        return processors

    async def teardown(self, resource: Processors) -> None:
        # Processors don't have an explicit cleanup method
        pass

    def _make_registered_reporters(
        self,
        spec: ProcessorsSpec,
    ) -> dict[str, AbstractReporter]:
        reporters: dict[str, AbstractReporter] = {}
        smtp_configs = spec.config.reporter.smtp
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
        self,
        spec: ProcessorsSpec,
        reporters: dict[str, AbstractReporter],
    ) -> dict[str, list[AbstractReporter]]:
        action_monitors: dict[str, list[AbstractReporter]] = {}
        action_monitor_configs = spec.config.reporter.action_monitors
        for action_monitor_conf in action_monitor_configs:
            reporter_name: str = action_monitor_conf.reporter
            try:
                reporter = reporters[reporter_name]
            except KeyError:
                # log.warning(f'Invalid Reporter: "{reporter_name}"')
                continue

            for action_type in action_monitor_conf.subscribed_actions:
                action_monitors.setdefault(action_type, []).append(reporter)

        return action_monitors