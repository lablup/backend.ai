from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import TYPE_CHECKING

from ai.backend.common.events.dispatcher import EventDispatcher

if TYPE_CHECKING:
    from ..api.context import RootContext


@actxmgr
async def event_dispatcher_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from ..event_dispatcher.dispatch import DispatcherArgs, Dispatchers

    root_ctx.event_dispatcher = EventDispatcher(
        root_ctx.message_queue,
        log_events=root_ctx.config_provider.config.debug.log_events,
        event_observer=root_ctx.metrics.event,
    )
    dispatchers = Dispatchers(
        DispatcherArgs(
            root_ctx.valkey_container_log,
            root_ctx.valkey_stat,
            root_ctx.valkey_stream,
            root_ctx.scheduler_dispatcher,
            root_ctx.sokovan_orchestrator.coordinator,
            root_ctx.scheduling_controller,
            root_ctx.sokovan_orchestrator.deployment_coordinator,
            root_ctx.sokovan_orchestrator.route_coordinator,
            root_ctx.repositories.scheduler.repository,
            root_ctx.event_hub,
            root_ctx.registry,
            root_ctx.db,
            root_ctx.idle_checker_host,
            root_ctx.event_dispatcher_plugin_ctx,
            root_ctx.repositories,
            lambda: root_ctx.processors,
            root_ctx.storage_manager,
            root_ctx.config_provider,
            use_sokovan=root_ctx.config_provider.config.manager.use_sokovan,
        )
    )
    dispatchers.dispatch(root_ctx.event_dispatcher)
    await root_ctx.event_dispatcher.start()
    yield
    await root_ctx.event_dispatcher.close()
