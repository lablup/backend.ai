from typing import Self, override

from aiohttp import web
from pydantic import ConfigDict

from ai.backend.common.api_handlers import MiddlewareParam
from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.services.processors import Processors


class ProcessorsCtx(MiddlewareParam):
    processors: Processors
    event_hub: EventHub
    event_fetcher: EventFetcher
    valkey_bgtask: ValkeyBgtaskClient

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        root_ctx: RootContext = request.app["_root.context"]
        return cls(
            processors=root_ctx.processors,
            event_hub=root_ctx.event_hub,
            event_fetcher=root_ctx.event_fetcher,
            valkey_bgtask=root_ctx.valkey_bgtask,
        )
