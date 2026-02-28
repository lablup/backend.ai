"""Backward-compatibility shim for the auto_scaling_rule module.

All auto-scaling rule handler logic has been migrated to:

* ``api.rest.auto_scaling_rule`` — AutoScalingRuleHandler + register_routes()

This module keeps ``create_app()`` so that the existing server bootstrap
(which iterates ``global_subapp_pkgs``) continues to work.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from aiohttp import web

from ai.backend.manager.api.types import CORSOptions

__all__ = ("create_app",)


def create_app(_default_cors_options: CORSOptions) -> tuple[web.Application, Iterable[Any]]:
    app = web.Application()
    app["prefix"] = "admin/auto-scaling-rules"
    app["api_versions"] = (4, 5)
    return app, []
