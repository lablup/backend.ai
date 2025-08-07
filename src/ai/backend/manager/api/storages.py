from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Iterable, Self, Tuple

import aiohttp_cors
from aiohttp import web
from pydantic import ConfigDict

from ai.backend.common.api_handlers import (
    APIResponse,
    BodyParam,
    MiddlewareParam,
    PathParam,
    api_handler,
)
from ai.backend.common.dto.manager.request import (
    CreateObjectStorageReq,
    ObjectStoragePathParam,
    UpdateObjectStorageReq,
)
from ai.backend.common.dto.manager.response import (
    DeleteObjectStorageResponse,
    ObjectStorageListResponse,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.object_storage.creator import ObjectStorageCreator
from ai.backend.manager.data.object_storage.modifier import ObjectStorageModifier
from ai.backend.manager.services.object_storage.actions.create import CreateObjectStorageAction
from ai.backend.manager.services.object_storage.actions.delete import DeleteObjectStorageAction
from ai.backend.manager.services.object_storage.actions.get import GetObjectStorageAction
from ai.backend.manager.services.object_storage.actions.list import ListObjectStorageAction
from ai.backend.manager.services.object_storage.actions.update import UpdateObjectStorageAction
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.types import OptionalState

if TYPE_CHECKING:
    from .context import RootContext

from .types import CORSOptions, WebMiddleware

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ProcessorsCtx(MiddlewareParam):
    processors: Processors

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        root_ctx: RootContext = request.app["_root.context"]

        return cls(
            processors=root_ctx.processors,
        )


class ObjectStorageHandler:
    @api_handler
    async def create_object_storage(
        self,
        processor_ctx: ProcessorsCtx,
        body: BodyParam[CreateObjectStorageReq],
    ) -> APIResponse:
        processors = processor_ctx.processors

        creator = ObjectStorageCreator(
            name=body.parsed.name,
            host=body.parsed.host,
            access_key=body.parsed.access_key,
            secret_key=body.parsed.secret_key,
            endpoint=body.parsed.endpoint,
            region=body.parsed.region,
            buckets=body.parsed.buckets,
        )

        action_result = await processors.object_storage.create.wait_for_complete(
            CreateObjectStorageAction(creator=creator)
        )

        response = action_result.result.to_dto()
        return APIResponse.build(HTTPStatus.CREATED, response)

    @api_handler
    async def list_object_storages(
        self,
        processor_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """List all object storage configurations."""
        processors = processor_ctx.processors

        action_result = await processors.object_storage.list_.wait_for_complete(
            ListObjectStorageAction()
        )

        storages = [data.to_dto() for data in action_result.data]
        response = ObjectStorageListResponse(
            storages=storages,
        )

        return APIResponse.build(HTTPStatus.OK, response)

    @api_handler
    async def get_object_storage(
        self,
        processor_ctx: ProcessorsCtx,
        path: PathParam[ObjectStoragePathParam],
    ) -> APIResponse:
        processors = processor_ctx.processors
        storage_id = path.parsed.storage_id

        action_result = await processors.object_storage.get.wait_for_complete(
            GetObjectStorageAction(storage_id=storage_id)
        )

        response = action_result.result.to_dto()
        return APIResponse.build(HTTPStatus.OK, response)

    @api_handler
    async def update_object_storage(
        self,
        processor_ctx: ProcessorsCtx,
        path: PathParam[ObjectStoragePathParam],
        body: BodyParam[UpdateObjectStorageReq],
    ) -> APIResponse:
        processors = processor_ctx.processors
        storage_id = path.parsed.storage_id
        req = body.parsed

        # Helper function to convert optional field to OptionalState
        def _to_optional_state(value):
            return OptionalState.update(value) if value is not None else OptionalState.nop()

        modifier = ObjectStorageModifier(
            name=_to_optional_state(req.name),
            host=_to_optional_state(req.host),
            access_key=_to_optional_state(req.access_key),
            secret_key=_to_optional_state(req.secret_key),
            endpoint=_to_optional_state(req.endpoint),
            region=_to_optional_state(req.region),
            buckets=_to_optional_state(req.buckets),
        )

        action_result = await processors.object_storage.update.wait_for_complete(
            UpdateObjectStorageAction(id=storage_id, modifier=modifier)
        )

        response = action_result.result.to_dto()
        return APIResponse.build(HTTPStatus.OK, response)

    @api_handler
    async def delete_object_storage(
        self,
        processor_ctx: ProcessorsCtx,
        path: PathParam[ObjectStoragePathParam],
    ) -> APIResponse:
        processors = processor_ctx.processors
        storage_id = path.parsed.storage_id

        await processors.object_storage.delete.wait_for_complete(
            DeleteObjectStorageAction(storage_id=storage_id)
        )

        response = DeleteObjectStorageResponse()

        return APIResponse.build(HTTPStatus.OK, response)


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4, 5)
    app["prefix"] = "storages"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    api_handlers = ObjectStorageHandler()

    cors.add(app.router.add_route("POST", "", api_handlers.create_object_storage))
    cors.add(app.router.add_route("GET", "", api_handlers.list_object_storages))
    cors.add(app.router.add_route("GET", "/{storage_id}", api_handlers.get_object_storage))
    cors.add(app.router.add_route("PATCH", "/{storage_id}", api_handlers.update_object_storage))
    cors.add(app.router.add_route("DELETE", "/{storage_id}", api_handlers.delete_object_storage))

    return app, []
