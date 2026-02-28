"""New-style artifact registry module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ArtifactRegistryHandler

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
) -> None:
    """Register artifact registry routes on the given RouteRegistry."""
    handler = ArtifactRegistryHandler(processors=processors)

    registry.add(
        "POST",
        "/scan",
        handler.scan_artifacts,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/delegation/scan",
        handler.delegate_scan_artifacts,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/delegation/import",
        handler.delegate_import_artifacts,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/search",
        handler.search_artifacts,
        middlewares=[auth_required],
    )
    registry.add(
        "GET",
        "/model/{model_id}",
        handler.scan_single_model,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/models/batch",
        handler.scan_models,
        middlewares=[auth_required],
    )
