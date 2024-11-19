from __future__ import annotations

from typing import TYPE_CHECKING, AsyncContextManager, Callable, TypeAlias

import aiohttp_cors
import attrs

if TYPE_CHECKING:
    from ai.backend.common.etcd import AsyncEtcd

    from .config import ServerConfig
    from .models.utils import ExtendedAsyncSAEngine
    from .plugin import WebappPluginContext


@attrs.define(slots=True, auto_attribs=True, init=False)
class RootContext:
    pidx: int
    db: ExtendedAsyncSAEngine
    etcd: AsyncEtcd
    local_config: ServerConfig
    webapp_plugin_ctx: WebappPluginContext

    cors_options: dict[str, aiohttp_cors.ResourceOptions]


CleanupContext: TypeAlias = Callable[["RootContext"], AsyncContextManager[None]]
