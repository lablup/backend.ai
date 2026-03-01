from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import register_artifact_registry_module

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.routing import RouteRegistry
    from ai.backend.manager.services.processors import Processors

__all__ = ["register_artifact_registry_module"]


def register_routes(registry: RouteRegistry, processors: Processors) -> None:
    """Backward-compatible shim — delegates to the old inline logic.

    The canonical entry-point is :func:`register_artifact_registry_module`;
    this wrapper exists only so that ``server.py`` keeps working until it is
    migrated to the new ``ModuleDeps`` convention.
    """
    from ai.backend.manager.api.rest.middleware.auth import auth_required

    from .handler import ArtifactRegistryHandler

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
