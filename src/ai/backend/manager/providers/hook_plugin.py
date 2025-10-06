from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import TYPE_CHECKING

from ai.backend.common.plugin.hook import ALL_COMPLETED, PASSED, HookPluginContext

if TYPE_CHECKING:
    from ..api.context import RootContext


@actxmgr
async def hook_plugin_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    ctx = HookPluginContext(
        root_ctx.etcd,
        root_ctx.config_provider.config.model_dump(by_alias=True),
    )
    root_ctx.hook_plugin_ctx = ctx
    await ctx.init(
        context=root_ctx,
        allowlist=root_ctx.config_provider.config.manager.allowed_plugins,
        blocklist=root_ctx.config_provider.config.manager.disabled_plugins,
    )
    hook_result = await ctx.dispatch(
        "ACTIVATE_MANAGER",
        (),
        return_when=ALL_COMPLETED,
    )
    if hook_result.status != PASSED:
        raise RuntimeError("Could not activate the manager instance.")
    yield
    await ctx.cleanup()
