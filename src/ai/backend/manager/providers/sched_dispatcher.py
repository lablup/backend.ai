from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..api.context import RootContext


@actxmgr
async def sched_dispatcher_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from ..scheduler.dispatcher import SchedulerDispatcher

    root_ctx.scheduler_dispatcher = await SchedulerDispatcher.create(
        root_ctx.config_provider,
        root_ctx.etcd,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
        root_ctx.registry,
        root_ctx.valkey_live,
        root_ctx.valkey_stat,
        root_ctx.repositories.schedule.repository,
    )
    yield
    await root_ctx.scheduler_dispatcher.close()
