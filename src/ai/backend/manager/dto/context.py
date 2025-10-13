from typing import TYPE_CHECKING, Self, override

from aiohttp import web
from pydantic import ConfigDict

from ai.backend.common.api_handlers import MiddlewareParam
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.services.processors import Processors

if TYPE_CHECKING:
    from ai.backend.manager.models.storage import StorageSessionManager


class ProcessorsCtx(MiddlewareParam):
    processors: Processors
    request: web.Request

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        root_ctx: RootContext = request.app["_root.context"]
        return cls(processors=root_ctx.processors, request=request)

    @property
    def storage_manager(self) -> "StorageSessionManager":
        """Get StorageSessionManager from root context."""
        root_ctx: RootContext = self.request.app["_root.context"]
        return root_ctx.storage_manager
