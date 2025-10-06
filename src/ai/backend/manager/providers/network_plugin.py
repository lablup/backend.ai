from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import TYPE_CHECKING

from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ..api.context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@actxmgr
async def network_plugin_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from ..plugin.network import NetworkPluginContext

    ctx = NetworkPluginContext(
        root_ctx.etcd,
        root_ctx.config_provider.config.model_dump(by_alias=True),
    )
    root_ctx.network_plugin_ctx = ctx
    await ctx.init(
        context=root_ctx,
        allowlist=root_ctx.config_provider.config.manager.allowed_plugins,
        blocklist=root_ctx.config_provider.config.manager.disabled_plugins,
    )
    log.info("NetworkPluginContext initialized with plugins: {}", list(ctx.plugins.keys()))
    yield
    await ctx.cleanup()
