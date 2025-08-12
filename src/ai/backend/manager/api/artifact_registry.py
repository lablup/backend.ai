from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Iterable, Tuple

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import (
    APIResponse,
    BodyParam,
    PathParam,
    api_handler,
)
from ai.backend.common.dto.manager.request import (
    ImportArtifactPathParam,
    ImportArtifactReq,
)
from ai.backend.common.dto.manager.response import (
    ImportArtifactResponse,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.services.artifact.actions.import_ import (
    ImportArtifactAction,
)
from ai.backend.manager.services.artifact.actions.types import ImportArtifactTarget
from ai.backend.manager.services.processors import Processors

if TYPE_CHECKING:
    from .context import RootContext

from .types import CORSOptions, WebMiddleware

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ArtifactRegistryHandler:
    _processors: Processors

    def __init__(self, processors: Processors) -> None:
        self._processors = processors

    @api_handler
    async def create(
        self,
        path: PathParam[ImportArtifactPathParam],
        body: BodyParam[ImportArtifactReq],
    ) -> APIResponse:
        """Import an artifact from external storage."""
        artifact_id = path.parsed.artifact_id
        storage_id = body.parsed.storage_id

        action = ImportArtifactAction(
            target=ImportArtifactTarget(
                artifact_id=artifact_id,
                storage_id=storage_id,
            )
        )

        result = await processors.artifact.import_.wait_for_complete(action)

        response = ImportArtifactResponse(
            artifact_id=str(result.result.id),
            name=result.result.name,
            version=result.result.version,
            size=result.result.size,
        )

        return APIResponse.build(HTTPStatus.OK, response)


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4, 5)
    app["prefix"] = "artifact-registries"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    root_context: RootContext = app["_root.context"]
    api_handlers = ArtifactRegistryHandler(root_context.processors)

    cors.add(app.router.add_route("POST", "/", api_handlers.create))

    return app, []
