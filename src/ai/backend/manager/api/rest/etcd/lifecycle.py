"""Etcd (config) sub-app lifecycle hooks.

Extracted from the legacy ``api/etcd.py`` module so that the
``rest/etcd`` package owns its own startup/shutdown concerns.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from aiohttp import web

if TYPE_CHECKING:
    from ai.backend.manager.api.context import RootContext


async def app_ctx(app: web.Application) -> AsyncGenerator[None, None]:
    root_ctx: RootContext = app["_root.context"]
    if root_ctx.pidx == 0:
        await root_ctx.config_provider.legacy_etcd_config_loader.register_myself()
    yield
    if root_ctx.pidx == 0:
        await root_ctx.config_provider.legacy_etcd_config_loader.deregister_myself()
