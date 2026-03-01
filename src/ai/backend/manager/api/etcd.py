"""Backward-compatibility shim for the etcd (config) module.

All handler logic has been migrated to:

* ``api.rest.etcd`` — EtcdHandler + route registration

This module retains ``app_ctx()`` because it is still imported by
``api.rest.etcd.registry`` for lifecycle management.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from aiohttp import web

if TYPE_CHECKING:
    from .context import RootContext


async def app_ctx(app: web.Application) -> AsyncGenerator[None, None]:
    root_ctx: RootContext = app["_root.context"]
    if root_ctx.pidx == 0:
        await root_ctx.config_provider.legacy_etcd_config_loader.register_myself()
    yield
    if root_ctx.pidx == 0:
        await root_ctx.config_provider.legacy_etcd_config_loader.deregister_myself()
