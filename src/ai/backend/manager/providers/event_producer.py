from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import TYPE_CHECKING

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.common.types import AGENTID_MANAGER

if TYPE_CHECKING:
    from ..api.context import RootContext


@actxmgr
async def event_producer_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    root_ctx.event_fetcher = EventFetcher(root_ctx.message_queue)
    root_ctx.event_producer = EventProducer(
        root_ctx.message_queue,
        source=AGENTID_MANAGER,
        log_events=root_ctx.config_provider.config.debug.log_events,
    )
    yield
    await root_ctx.event_producer.close()
    await asyncio.sleep(0.2)
