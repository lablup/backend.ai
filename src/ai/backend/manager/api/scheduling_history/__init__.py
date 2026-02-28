"""Backward-compatibility shim for the scheduling history module.

All scheduling history handler logic has been migrated to:

* ``api.rest.scheduling_history`` — SchedulingHistoryHandler + register_routes()

This module keeps ``create_app()`` so that the existing server bootstrap
(which iterates ``global_subapp_pkgs``) continues to work.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from aiohttp import web

from ai.backend.manager.api.types import CORSOptions


def create_app(_default_cors_options: CORSOptions) -> tuple[web.Application, Iterable[Any]]:
    app = web.Application()
    app["prefix"] = "scheduling-history"
    app["api_versions"] = (4, 5)
    return app, []
