from typing import Self, override

from aiohttp import web
from pydantic import ConfigDict

from ai.backend.common.api_handlers import MiddlewareParam
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.services.processors import Processors


class ProcessorsCtx(MiddlewareParam):
    processors: Processors

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        root_ctx: RootContext = request.app["_root.context"]
        return cls(processors=root_ctx.processors)


class StorageSessionManagerCtx(MiddlewareParam):
    storage_session_manager: StorageSessionManager

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        root_ctx: RootContext = request.app["_root.context"]
        return cls(storage_session_manager=root_ctx.storage_manager)
