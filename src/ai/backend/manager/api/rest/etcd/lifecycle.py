"""Etcd (config) sub-app lifecycle hooks.

Extracted from the legacy ``api/etcd.py`` module so that the
``rest/etcd`` package owns its own startup/shutdown concerns.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable
from typing import TYPE_CHECKING

from aiohttp import web

if TYPE_CHECKING:
    from ai.backend.manager.config.provider import ManagerConfigProvider


def make_app_ctx(
    pidx: int,
    config_provider: ManagerConfigProvider,
) -> Callable[[web.Application], AsyncGenerator[None, None]]:
    async def app_ctx(_app: web.Application) -> AsyncGenerator[None, None]:
        if pidx == 0:
            await config_provider.legacy_etcd_config_loader.register_myself()
        yield
        if pidx == 0:
            await config_provider.legacy_etcd_config_loader.deregister_myself()

    return app_ctx
