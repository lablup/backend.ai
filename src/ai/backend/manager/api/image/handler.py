"""
REST API handlers for image management.
Provides admin endpoints for searching, getting, rescanning, aliasing, and managing images.
"""

from __future__ import annotations

from collections.abc import Iterable
from http import HTTPStatus

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, api_handler
from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.image import (
    AliasImageRequest,
    AliasImageResponse,
    DealiasImageRequest,
    ForgetImageRequest,
    ForgetImageResponse,
    GetImageResponse,
    PaginationInfo,
    PurgeImageRequest,
    PurgeImageResponse,
    RescanImagesRequest,
    RescanImagesResponse,
    SearchImagesRequest,
    SearchImagesResponse,
)
from ai.backend.common.types import ImageID
from ai.backend.manager.api.auth import auth_required_for_method
from ai.backend.manager.api.types import CORSOptions, WebMiddleware
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.dto.image_request import GetImagePathParam
from ai.backend.manager.services.image.actions.alias_image import AliasImageByIdAction
from ai.backend.manager.services.image.actions.dealias_image import DealiasImageAction
from ai.backend.manager.services.image.actions.forget_image import ForgetImageByIdAction
from ai.backend.manager.services.image.actions.get_images import GetImageByIdAction
from ai.backend.manager.services.image.actions.purge_images import PurgeImageByIdAction
from ai.backend.manager.services.image.actions.scan_image import ScanImageAction
from ai.backend.manager.services.image.actions.search_images import SearchImagesAction

from .adapter import ImageAdapter

__all__ = ("create_app",)


class ImageAPIHandler:
    """REST API handler class for image management operations."""

    def __init__(self) -> None:
        self._adapter = ImageAdapter()

    @staticmethod
    def _check_superadmin() -> None:
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can manage images.")

    @auth_required_for_method
    @api_handler
    async def search(
        self,
        body: BodyParam[SearchImagesRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search images with filters, orders, and pagination."""
        processors = processors_ctx.processors
        self._check_superadmin()

        querier = self._adapter.build_querier(body.parsed)

        action_result = await processors.image.search_images.wait_for_complete(
            SearchImagesAction(querier=querier)
        )

        resp = SearchImagesResponse(
            items=[self._adapter.convert_to_dto(img) for img in action_result.data],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get(
        self,
        path: PathParam[GetImagePathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get a single image by ID."""
        processors = processors_ctx.processors
        self._check_superadmin()

        action_result = await processors.image.get_image_by_id.wait_for_complete(
            GetImageByIdAction(image_id=ImageID(path.parsed.image_id), image_status=None)
        )

        resp = GetImageResponse(
            item=self._adapter.convert_detailed_to_dto(
                action_result.image_with_agent_install_status.image
            )
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def rescan(
        self,
        body: BodyParam[RescanImagesRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Rescan an image from the registry."""
        processors = processors_ctx.processors
        self._check_superadmin()

        action_result = await processors.image.scan_image.wait_for_complete(
            ScanImageAction(canonical=body.parsed.canonical, architecture=body.parsed.architecture)
        )

        resp = RescanImagesResponse(
            item=self._adapter.convert_to_dto(action_result.image),
            errors=action_result.errors,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def alias(
        self,
        body: BodyParam[AliasImageRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Create an image alias."""
        processors = processors_ctx.processors
        self._check_superadmin()

        action_result = await processors.image.alias_image_by_id.wait_for_complete(
            AliasImageByIdAction(
                image_id=ImageID(body.parsed.image_id),
                alias=body.parsed.alias,
            )
        )

        resp = AliasImageResponse(
            alias_id=action_result.image_alias.id,
            alias=action_result.image_alias.alias,
            image_id=action_result.image_id,
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def dealias(
        self,
        body: BodyParam[DealiasImageRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Remove an image alias."""
        processors = processors_ctx.processors
        self._check_superadmin()

        action_result = await processors.image.dealias_image.wait_for_complete(
            DealiasImageAction(alias=body.parsed.alias)
        )

        resp = AliasImageResponse(
            alias_id=action_result.image_alias.id,
            alias=action_result.image_alias.alias,
            image_id=action_result.image_id,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def forget(
        self,
        body: BodyParam[ForgetImageRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Forget (soft-delete) an image."""
        processors = processors_ctx.processors
        self._check_superadmin()

        action_result = await processors.image.forget_image_by_id.wait_for_complete(
            ForgetImageByIdAction(image_id=ImageID(body.parsed.image_id))
        )

        resp = ForgetImageResponse(
            item=self._adapter.convert_to_dto(action_result.image),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def purge(
        self,
        body: BodyParam[PurgeImageRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Purge (hard-delete) an image."""
        processors = processors_ctx.processors
        self._check_superadmin()

        action_result = await processors.image.purge_image_by_id.wait_for_complete(
            PurgeImageByIdAction(image_id=ImageID(body.parsed.image_id))
        )

        resp = PurgeImageResponse(
            item=self._adapter.convert_to_dto(action_result.image),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "admin/images"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    api_handler = ImageAPIHandler()

    cors.add(app.router.add_route("POST", "/search", api_handler.search))
    cors.add(app.router.add_route("GET", "/{image_id}", api_handler.get))
    cors.add(app.router.add_route("POST", "/rescan", api_handler.rescan))
    cors.add(app.router.add_route("POST", "/alias", api_handler.alias))
    cors.add(app.router.add_route("POST", "/dealias", api_handler.dealias))
    cors.add(app.router.add_route("POST", "/forget", api_handler.forget))
    cors.add(app.router.add_route("POST", "/purge", api_handler.purge))

    return app, []
