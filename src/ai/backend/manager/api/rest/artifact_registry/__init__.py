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
        "/artifact-registries/scan",
        handler.scan_artifacts,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/artifact-registries/delegation/scan",
        handler.delegate_scan_artifacts,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/artifact-registries/delegation/import",
        handler.delegate_import_artifacts,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/artifact-registries/search",
        handler.search_artifacts,
        middlewares=[auth_required],
    )
    registry.add(
        "GET",
        "/artifact-registries/model/{model_id}",
        handler.scan_single_model,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/artifact-registries/models/batch",
        handler.scan_models,
        middlewares=[auth_required],
    )
