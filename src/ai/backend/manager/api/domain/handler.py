"""Backward-compatibility shim for the domain module.

Handler logic has been migrated to ``api.rest.domain.handler.DomainHandler``.
This module keeps ``create_app()`` functional so that ``server.py`` can still
load it as a legacy subapp.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from aiohttp import web

from ai.backend.manager.api.types import CORSOptions

__all__ = ("create_app",)


def create_app(
    _default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[Any]]:
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "admin/domains"
    return app, []
