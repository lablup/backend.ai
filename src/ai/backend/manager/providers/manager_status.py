from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..api.context import RootContext


@actxmgr
async def manager_status_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from ai.backend.logging import BraceStyleAdapter

    from ..api import ManagerStatus

    log = BraceStyleAdapter(__import__("logging").getLogger(__spec__.name))

    if root_ctx.pidx == 0:
        mgr_status = await root_ctx.config_provider.legacy_etcd_config_loader.get_manager_status()
        if mgr_status is None or mgr_status not in (ManagerStatus.RUNNING, ManagerStatus.FROZEN):
            # legacy transition: we now have only RUNNING or FROZEN for HA setup.
            await root_ctx.config_provider.legacy_etcd_config_loader.update_manager_status(
                ManagerStatus.RUNNING
            )
            mgr_status = ManagerStatus.RUNNING
        log.info("Manager status: {}", mgr_status)
        tz = root_ctx.config_provider.config.system.timezone
        log.info("Configured timezone: {}", tz.tzname(datetime.now()))
    yield
