"""VFolder sub-app lifecycle hooks.

Extracted from the legacy ``api/vfolder.py`` module so that the
``rest/vfolder`` package owns its own startup/shutdown concerns.
"""

from __future__ import annotations

import logging
from types import TracebackType

import aiotools
import attrs
from aiohttp import web

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


async def storage_task_exception_handler(
    exc_type: type[BaseException],  # noqa: ARG001
    exc_obj: BaseException,
    exc_tb: TracebackType,  # noqa: ARG001
) -> None:
    log.exception("Error while removing vFolder", exc_info=exc_obj)


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    database_ptask_group: aiotools.PersistentTaskGroup
    storage_ptask_group: aiotools.PersistentTaskGroup


async def init(app: web.Application) -> None:
    app_ctx: PrivateContext = app["folders.context"]
    app_ctx.database_ptask_group = aiotools.PersistentTaskGroup()
    app_ctx.storage_ptask_group = aiotools.PersistentTaskGroup(
        exception_handler=storage_task_exception_handler
    )


async def shutdown(app: web.Application) -> None:
    app_ctx: PrivateContext = app["folders.context"]
    await app_ctx.database_ptask_group.shutdown()
    await app_ctx.storage_ptask_group.shutdown()
