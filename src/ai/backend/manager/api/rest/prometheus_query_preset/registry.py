"""Prometheus Query Preset module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import PrometheusQueryPresetHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_prometheus_query_preset_routes(
    handler: PrometheusQueryPresetHandler, route_deps: RouteDeps
) -> RouteRegistry:
    """Build the prometheus query preset sub-application."""
    reg = RouteRegistry.create("resource/prometheus-query-definitions", route_deps.cors_options)

    # CRUD endpoints (superadmin only)
    reg.add("POST", "", handler.create_preset, middlewares=[superadmin_required])
    reg.add("POST", "/search", handler.search_presets, middlewares=[superadmin_required])
    reg.add("GET", "/{id}", handler.get_preset, middlewares=[superadmin_required])
    reg.add("PATCH", "/{id}", handler.modify_preset, middlewares=[superadmin_required])
    reg.add("DELETE", "/{id}", handler.delete_preset, middlewares=[superadmin_required])

    # Execute endpoint (superadmin only)
    reg.add("POST", "/{id}/execute", handler.execute_preset, middlewares=[superadmin_required])

    return reg
