"""Backward-compatible create_app() shim for the artifact module.

All artifact handler logic has been migrated to:

* ``api.rest.artifact.handler`` — ArtifactHandler class
* ``api.rest.artifact`` — route registration

This module keeps the ``create_app()`` entry-point so that
``server.py`` continues to mount the sub-application without modification.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from aiohttp import web

from ai.backend.manager.api.rest.artifact.handler import ArtifactHandler
from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .types import CORSOptions, WebMiddleware

if TYPE_CHECKING:
    from ai.backend.manager.api.context import RootContext


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4, 5)
    app["prefix"] = "artifacts"

    handler = ArtifactHandler()
    registry = RouteRegistry(app, default_cors_options)
    _middlewares = [auth_required]

    registry.add("POST", "/revisions/cleanup", handler.cleanup_artifacts, middlewares=_middlewares)
    registry.add(
        "POST",
        "/revisions/{artifact_revision_id}/approval",
        handler.approve_artifact_revision,
        middlewares=_middlewares,
    )
    registry.add(
        "POST",
        "/revisions/{artifact_revision_id}/rejection",
        handler.reject_artifact_revision,
        middlewares=_middlewares,
    )
    registry.add("POST", "/task/cancel", handler.cancel_import_artifact, middlewares=_middlewares)
    registry.add("POST", "/import", handler.import_artifacts, middlewares=_middlewares)
    registry.add("PATCH", "/{artifact_id}", handler.update_artifact, middlewares=_middlewares)
    registry.add(
        "GET",
        "/revisions/{artifact_revision_id}/readme",
        handler.get_artifact_revision_readme,
        middlewares=_middlewares,
    )
    registry.add(
        "GET",
        "/revisions/{artifact_revision_id}/verification-result",
        handler.get_artifact_revision_verification_result,
        middlewares=_middlewares,
    )
    registry.add(
        "GET",
        "/revisions/{artifact_revision_id}/download-progress",
        handler.get_download_progress,
        middlewares=_middlewares,
    )

    async def _bind_processors(app: web.Application) -> None:
        root_ctx: RootContext = app["_root.context"]
        handler.bind_processors(root_ctx.processors)

    app.on_startup.insert(0, _bind_processors)

    return app, []
