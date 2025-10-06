from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import TYPE_CHECKING

from ai.backend.common.events.hub.hub import EventHub

if TYPE_CHECKING:
    from ..api.context import RootContext


@actxmgr
async def event_hub_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    root_ctx.event_hub = EventHub()
    yield
    await root_ctx.event_hub.shutdown()
