from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import TYPE_CHECKING

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


type CleanupContext = Callable[["RootContext"], AbstractAsyncContextManager[None]]
