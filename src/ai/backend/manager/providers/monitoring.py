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
async def monitoring_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from ..plugin.monitor import ManagerErrorPluginContext, ManagerStatsPluginContext

    ectx = ManagerErrorPluginContext(
        root_ctx.etcd, root_ctx.config_provider.config.model_dump(by_alias=True)
    )
    sctx = ManagerStatsPluginContext(
        root_ctx.etcd, root_ctx.config_provider.config.model_dump(by_alias=True)
    )
    init_success = False

    try:
        await ectx.init(
            context={"_root.context": root_ctx},
            allowlist=root_ctx.config_provider.config.manager.allowed_plugins,
        )
        await sctx.init(allowlist=root_ctx.config_provider.config.manager.allowed_plugins)
    except Exception:
        log.error("Failed to initialize monitoring plugins")
    else:
        init_success = True
        root_ctx.error_monitor = ectx
        root_ctx.stats_monitor = sctx
    yield
    if init_success:
        await sctx.cleanup()
        await ectx.cleanup()
