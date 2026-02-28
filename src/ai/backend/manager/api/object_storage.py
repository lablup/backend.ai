"""Backward-compatibility shim for the object storage module.

All object storage handler logic has been migrated to:

* ``api.rest.object_storage`` — ObjectStorageHandler + register_routes()

This module keeps ``create_app()`` so that the existing server bootstrap
(which iterates ``global_subapp_pkgs``) continues to work.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from aiohttp import web

from .types import CORSOptions


def create_app(_default_cors_options: CORSOptions) -> tuple[web.Application, Iterable[Any]]:
    app = web.Application()
    app["prefix"] = "object-storages"
    app["api_versions"] = (1, 2, 3, 4, 5)
    return app, []
