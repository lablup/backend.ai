"""Artifact registry module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ArtifactRegistryHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_artifact_registry_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the artifact registry sub-application."""
    reg = RouteRegistry.create("artifact-registries", deps.cors_options)
    handler = ArtifactRegistryHandler(processors=deps.processors)

    reg.add(
        "POST",
        "/scan",
        handler.scan_artifacts,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/delegation/scan",
        handler.delegate_scan_artifacts,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/delegation/import",
        handler.delegate_import_artifacts,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/search",
        handler.search_artifacts,
        middlewares=[auth_required],
    )
    reg.add(
        "GET",
        "/model/{model_id}",
        handler.scan_single_model,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/models/batch",
        handler.scan_models,
        middlewares=[auth_required],
    )
    return reg
