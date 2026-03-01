"""Backward-compatibility shim for the scaling_group module.

All scaling group handler logic has been migrated to:

* ``api.rest.scaling_group`` — ScalingGroupHandler + route registration

This module keeps ``create_app()`` so that the existing server bootstrap
(which iterates ``global_subapp_pkgs``) continues to work.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from aiohttp import web

from .types import CORSOptions


def create_app(
    _default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[Any]]:
    app = web.Application()
    app["prefix"] = "scaling-groups"
    app["api_versions"] = (2, 3, 4)
    return app, []
