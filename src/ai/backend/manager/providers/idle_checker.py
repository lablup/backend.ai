from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..api.context import RootContext


@actxmgr
async def idle_checker_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from ..idle import init_idle_checkers

    root_ctx.idle_checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.config_provider,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    await root_ctx.idle_checker_host.start()
    yield
    await root_ctx.idle_checker_host.shutdown()
