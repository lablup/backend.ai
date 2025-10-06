from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import TYPE_CHECKING

from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.manager.reporters.base import AbstractReporter

    from ..api.context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def _make_registered_reporters(
    root_ctx: RootContext,
) -> dict[str, AbstractReporter]:
    from ..reporters.smtp import SMTPReporter, SMTPSenderArgs
    from ..types import SMTPTriggerPolicy

    reporters: dict[str, AbstractReporter] = {}
    smtp_configs = root_ctx.config_provider.config.reporter.smtp
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
    root_ctx: RootContext,
    reporters: dict[str, AbstractReporter],
) -> dict[str, list[AbstractReporter]]:
    action_monitors: dict[str, list[AbstractReporter]] = {}
    action_monitor_configs = root_ctx.config_provider.config.reporter.action_monitors
    for action_monitor_conf in action_monitor_configs:
        reporter_name: str = action_monitor_conf.reporter
        try:
            reporter = reporters[reporter_name]
        except KeyError:
            log.warning(f'Invalid Reporter: "{reporter_name}"')
            continue

        for action_type in action_monitor_conf.subscribed_actions:
            action_monitors.setdefault(action_type, []).append(reporter)

    return action_monitors


@actxmgr
async def processors_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from ..actions.monitors.audit_log import AuditLogMonitor
    from ..actions.monitors.prometheus import PrometheusMonitor
    from ..actions.monitors.reporter import ReporterMonitor
    from ..reporters.hub import ReporterHub, ReporterHubArgs
    from ..services.processors import ProcessorArgs, Processors, ServiceArgs

    registered_reporters = _make_registered_reporters(root_ctx)
    action_reporters = _make_action_reporters(root_ctx, registered_reporters)
    reporter_hub = ReporterHub(
        ReporterHubArgs(
            reporters=action_reporters,
        )
    )
    reporter_monitor = ReporterMonitor(reporter_hub)
    prometheus_monitor = PrometheusMonitor()
    audit_log_monitor = AuditLogMonitor(root_ctx.db)
    root_ctx.processors = Processors.create(
        ProcessorArgs(
            service_args=ServiceArgs(
                db=root_ctx.db,
                repositories=root_ctx.repositories,
                etcd=root_ctx.etcd,
                config_provider=root_ctx.config_provider,
                storage_manager=root_ctx.storage_manager,
                valkey_stat_client=root_ctx.valkey_stat,
                valkey_live=root_ctx.valkey_live,
                event_fetcher=root_ctx.event_fetcher,
                background_task_manager=root_ctx.background_task_manager,
                event_hub=root_ctx.event_hub,
                agent_registry=root_ctx.registry,
                error_monitor=root_ctx.error_monitor,
                idle_checker_host=root_ctx.idle_checker_host,
                event_dispatcher=root_ctx.event_dispatcher,
                hook_plugin_ctx=root_ctx.hook_plugin_ctx,
                scheduling_controller=root_ctx.scheduling_controller,
                deployment_controller=root_ctx.deployment_controller,
                event_producer=root_ctx.event_producer,
                agent_cache=root_ctx.agent_cache,
            )
        ),
        [reporter_monitor, prometheus_monitor, audit_log_monitor],
    )
    yield
