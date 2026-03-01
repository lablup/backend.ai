"""Artifact module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ArtifactHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_artifact_module(deps: ModuleDeps) -> RouteRegistry:
    """Build the artifact sub-application."""
    reg = RouteRegistry.create("artifacts", deps.cors_options)
    handler = ArtifactHandler(processors=deps.processors)

    reg.add(
        "POST",
        "/revisions/cleanup",
        handler.cleanup_artifacts,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/revisions/{artifact_revision_id}/approval",
        handler.approve_artifact_revision,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/revisions/{artifact_revision_id}/rejection",
        handler.reject_artifact_revision,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/task/cancel",
        handler.cancel_import_artifact,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/import",
        handler.import_artifacts,
        middlewares=[auth_required],
    )
    reg.add(
        "PATCH",
        "/{artifact_id}",
        handler.update_artifact,
        middlewares=[auth_required],
    )
    reg.add(
        "GET",
        "/revisions/{artifact_revision_id}/readme",
        handler.get_artifact_revision_readme,
        middlewares=[auth_required],
    )
    reg.add(
        "GET",
        "/revisions/{artifact_revision_id}/verification-result",
        handler.get_artifact_revision_verification_result,
        middlewares=[auth_required],
    )
    reg.add(
        "GET",
        "/revisions/{artifact_revision_id}/download-progress",
        handler.get_download_progress,
        middlewares=[auth_required],
    )
    return reg
