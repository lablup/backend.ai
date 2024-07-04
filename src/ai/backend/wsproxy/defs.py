from typing import TYPE_CHECKING, AsyncContextManager, Callable, TypeAlias
from uuid import UUID

import aiohttp_cors
import attrs

from .config import ServerConfig

if TYPE_CHECKING:
    from .proxy.frontend.abc import AbstractFrontend


@attrs.define(slots=True, auto_attribs=True, init=False)
class RootContext:
    pidx: int
    proxy_frontend: "AbstractFrontend"
    worker_id: UUID
    local_config: ServerConfig
    cors_options: dict[str, aiohttp_cors.ResourceOptions]


CleanupContext: TypeAlias = Callable[["RootContext"], AsyncContextManager[None]]
