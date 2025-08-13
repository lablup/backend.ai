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
    AssociateArtifactWithStorageReq,
    DeleteArtifactPathParam,
    DisassociateArtifactWithStorageReq,
    ImportArtifactPathParam,
    ImportArtifactReq,
    UpdateArtifactPathParam,
    UpdateArtifactReq,
)
from ai.backend.common.dto.manager.response import (
    AssociateArtifactWithStorageResponse,
    AssociationArtifactStorageResponse,
    DeleteArtifactResponse,
    DisassociateArtifactWithStorageResponse,
    ImportArtifactResponse,
    UpdateArtifactResponse,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.services.artifact.actions.associate_with_storage import (
    AssociateWithStorageAction,
)
from ai.backend.manager.services.artifact.actions.disassociate_with_storage import (
    DisassociateWithStorageAction,
)
from ai.backend.manager.services.artifact.actions.import_ import (
    ImportArtifactAction,
)
from ai.backend.manager.services.artifact.actions.types import ImportArtifactTarget
from ai.backend.manager.services.processors import Processors

if TYPE_CHECKING:
    from .context import RootContext

from .types import CORSOptions, WebMiddleware

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ArtifactHandler:
    _processors: Processors

    def __init__(self, processors: Processors):
        self._processors = processors

    @api_handler
    async def import_artifact(
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

        result = await self._processors.artifact.import_.wait_for_complete(action)

        response = ImportArtifactResponse(
            artifact_id=str(result.result.id),
            name=result.result.name,
            version=result.result.version,
            size=result.result.size,
        )

        return APIResponse.build(HTTPStatus.OK, response)

    @api_handler
    async def update_artifact(
        self,
        path: PathParam[UpdateArtifactPathParam],
        body: BodyParam[UpdateArtifactReq],
    ) -> APIResponse:
        """Update an artifact's metadata."""
        artifact_id = path.parsed.artifact_id

        # TODO: Implement update functionality
        # For now, return a placeholder response
        response = UpdateArtifactResponse(
            artifact_id=str(artifact_id),
            name="placeholder",
            version="1.0.0",
        )

        return APIResponse.build(HTTPStatus.OK, response)

    @api_handler
    async def delete_artifact(
        self,
        path: PathParam[DeleteArtifactPathParam],
    ) -> APIResponse:
        """Delete an artifact."""
        artifact_id = path.parsed.artifact_id

        # TODO: Implement delete functionality
        # For now, return a placeholder response
        response = DeleteArtifactResponse(
            artifact_id=str(artifact_id),
            message=f"Artifact {artifact_id} deleted successfully",
        )

        return APIResponse.build(HTTPStatus.OK, response)

    @api_handler
    async def associate_artifact_with_storage(
        self,
        body: BodyParam[AssociateArtifactWithStorageReq],
    ) -> APIResponse:
        """Associate an artifact with a storage."""
        artifact_id = body.parsed.artifact_id
        storage_id = body.parsed.storage_id

        action = AssociateWithStorageAction(
            artifact_id=artifact_id,
            storage_id=storage_id,
        )

        result = await self._processors.artifact.associate_with_storage.wait_for_complete(action)

        association = AssociationArtifactStorageResponse(
            id=str(result.result.id),
            artifact_id=str(result.result.artifact_id),
            storage_id=str(result.result.storage_id),
        )
        response = AssociateArtifactWithStorageResponse(
            association=association,
            message=f"Artifact {artifact_id} associated with storage {storage_id}",
        )

        return APIResponse.build(HTTPStatus.CREATED, response)

    @api_handler
    async def disassociate_artifact_with_storage(
        self,
        body: BodyParam[DisassociateArtifactWithStorageReq],
    ) -> APIResponse:
        """Disassociate an artifact from a storage."""
        artifact_id = body.parsed.artifact_id
        storage_id = body.parsed.storage_id

        action = DisassociateWithStorageAction(
            artifact_id=artifact_id,
            storage_id=storage_id,
        )

        result = await self._processors.artifact.disassociate_with_storage.wait_for_complete(action)

        association = AssociationArtifactStorageResponse(
            id=str(result.result.id),
            artifact_id=str(result.result.artifact_id),
            storage_id=str(result.result.storage_id),
        )
        response = DisassociateArtifactWithStorageResponse(
            association=association,
            message=f"Artifact {artifact_id} disassociated from storage {storage_id}",
        )

        return APIResponse.build(HTTPStatus.OK, response)


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4, 5)
    app["prefix"] = "artifact"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    root_context: RootContext = app["_root.context"]
    api_handlers = ArtifactHandler(root_context.processors)

    cors.add(app.router.add_route("POST", "/{artifact_id}/import", api_handlers.import_artifact))
    cors.add(app.router.add_route("PATCH", "/{artifact_id}", api_handlers.update_artifact))
    cors.add(app.router.add_route("DELETE", "/{artifact_id}", api_handlers.delete_artifact))
    cors.add(
        app.router.add_route("POST", "/associations", api_handlers.associate_artifact_with_storage)
    )
    cors.add(
        app.router.add_route(
            "DELETE", "/associations", api_handlers.disassociate_artifact_with_storage
        )
    )

    return app, []
