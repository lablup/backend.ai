"""Backward-compatible shim for the service (model serving) module.

The actual handler logic has been migrated to
``ai.backend.manager.api.rest.service.handler.ServiceHandler``.

``PrivateContext``, ``init``, and ``shutdown`` are preserved as they are used
as lifecycle hooks by ``rest/service/registry.py``.
``ServiceFilterModel`` is re-exported for backward compatibility (used by tests).

The ``create_app()`` shim has been removed because
``global_subapp_pkgs`` is no longer used by the server bootstrap.
"""

from __future__ import annotations

import logging

import aiotools
import attrs
from aiohttp import web

from ai.backend.common.dto.manager.model_serving.request import ServiceFilterModel
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__name__))

# Re-export for backward compatibility (used by adapter.py)
__all__ = ("ServiceFilterModel",)


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    database_ptask_group: aiotools.PersistentTaskGroup


async def init(app: web.Application) -> None:
    app_ctx: PrivateContext = app["services.context"]
    app_ctx.database_ptask_group = aiotools.PersistentTaskGroup()


async def shutdown(app: web.Application) -> None:
    app_ctx: PrivateContext = app["services.context"]
    await app_ctx.database_ptask_group.shutdown()
