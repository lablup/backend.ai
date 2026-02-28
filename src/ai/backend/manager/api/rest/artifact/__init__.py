"""New-style artifact module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ArtifactHandler

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
) -> None:
    """Register artifact routes on the given RouteRegistry."""
    handler = ArtifactHandler(processors=processors)

    registry.add(
        "POST",
        "/revisions/cleanup",
        handler.cleanup_artifacts,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/revisions/{artifact_revision_id}/approval",
        handler.approve_artifact_revision,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/revisions/{artifact_revision_id}/rejection",
        handler.reject_artifact_revision,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/task/cancel",
        handler.cancel_import_artifact,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/import",
        handler.import_artifacts,
        middlewares=[auth_required],
    )
    registry.add(
        "PATCH",
        "/{artifact_id}",
        handler.update_artifact,
        middlewares=[auth_required],
    )
    registry.add(
        "GET",
        "/revisions/{artifact_revision_id}/readme",
        handler.get_artifact_revision_readme,
        middlewares=[auth_required],
    )
    registry.add(
        "GET",
        "/revisions/{artifact_revision_id}/verification-result",
        handler.get_artifact_revision_verification_result,
        middlewares=[auth_required],
    )
    registry.add(
        "GET",
        "/revisions/{artifact_revision_id}/download-progress",
        handler.get_download_progress,
        middlewares=[auth_required],
    )
