from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import TYPE_CHECKING

from ai.backend.common.plugin.event import EventDispatcherPluginContext

if TYPE_CHECKING:
    from ..api.context import RootContext


@actxmgr
async def event_dispatcher_plugin_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    ctx = EventDispatcherPluginContext(
        root_ctx.etcd,
        root_ctx.config_provider.config.model_dump(by_alias=True),
    )
    root_ctx.event_dispatcher_plugin_ctx = ctx
    await ctx.init(
        context=root_ctx,
        allowlist=root_ctx.config_provider.config.manager.allowed_plugins,
        blocklist=root_ctx.config_provider.config.manager.disabled_plugins,
    )
    yield
    await ctx.cleanup()
