"""Service (model serving) sub-app lifecycle hooks.

Extracted from the legacy ``api/service.py`` module so that the
``rest/service`` package owns its own startup/shutdown concerns.
"""

from __future__ import annotations

import logging

import aiotools
import attrs
from aiohttp import web

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    database_ptask_group: aiotools.PersistentTaskGroup


async def init(app: web.Application) -> None:
    app_ctx: PrivateContext = app["services.context"]
    app_ctx.database_ptask_group = aiotools.PersistentTaskGroup()


async def shutdown(app: web.Application) -> None:
    app_ctx: PrivateContext = app["services.context"]
    await app_ctx.database_ptask_group.shutdown()
