"""Image handler class using constructor dependency injection."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
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
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.dto.image_request import GetImagePathParam
from ai.backend.manager.services.image.actions.alias_image import AliasImageByIdAction
from ai.backend.manager.services.image.actions.dealias_image import DealiasImageAction
from ai.backend.manager.services.image.actions.forget_image import ForgetImageByIdAction
from ai.backend.manager.services.image.actions.get_images import GetImageByIdAction
from ai.backend.manager.services.image.actions.purge_images import PurgeImageByIdAction
from ai.backend.manager.services.image.actions.scan_image import ScanImageAction
from ai.backend.manager.services.image.actions.search_images import SearchImagesAction
from ai.backend.manager.services.image.processors import ImageProcessors

from .adapter import ImageAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ImageHandler:
    """Image API handler with constructor-injected dependencies."""

    def __init__(self, *, image: ImageProcessors) -> None:
        self._image = image
        self._adapter = ImageAdapter()

    async def search(
        self,
        body: BodyParam[SearchImagesRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Search images with filters, orders, and pagination."""
        log.info("SEARCH (ak:{})", ctx.access_key)
        querier = self._adapter.build_querier(body.parsed)
        action_result = await self._image.search_images.wait_for_complete(
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

    async def get(
        self,
        path: PathParam[GetImagePathParam],
        ctx: UserContext,
    ) -> APIResponse:
        """Get a single image by ID."""
        log.info("GET (ak:{}, image_id:{})", ctx.access_key, path.parsed.image_id)
        action_result = await self._image.get_image_by_id.wait_for_complete(
            GetImageByIdAction(image_id=ImageID(path.parsed.image_id), image_status=None)
        )
        resp = GetImageResponse(
            item=self._adapter.convert_detailed_to_dto(
                action_result.image_with_agent_install_status.image
            )
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def rescan(
        self,
        body: BodyParam[RescanImagesRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Rescan an image from the registry."""
        log.info("RESCAN (ak:{})", ctx.access_key)
        action_result = await self._image.scan_image.wait_for_complete(
            ScanImageAction(canonical=body.parsed.canonical, architecture=body.parsed.architecture)
        )
        resp = RescanImagesResponse(
            item=self._adapter.convert_to_dto(action_result.image),
            errors=action_result.errors,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def alias(
        self,
        body: BodyParam[AliasImageRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Create an image alias."""
        log.info("ALIAS (ak:{})", ctx.access_key)
        action_result = await self._image.alias_image_by_id.wait_for_complete(
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

    async def dealias(
        self,
        body: BodyParam[DealiasImageRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Remove an image alias."""
        log.info("DEALIAS (ak:{})", ctx.access_key)
        action_result = await self._image.dealias_image.wait_for_complete(
            DealiasImageAction(alias=body.parsed.alias)
        )
        resp = AliasImageResponse(
            alias_id=action_result.image_alias.id,
            alias=action_result.image_alias.alias,
            image_id=action_result.image_id,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def forget(
        self,
        body: BodyParam[ForgetImageRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Forget (soft-delete) an image."""
        log.info("FORGET (ak:{})", ctx.access_key)
        action_result = await self._image.forget_image_by_id.wait_for_complete(
            ForgetImageByIdAction(image_id=ImageID(body.parsed.image_id))
        )
        resp = ForgetImageResponse(
            item=self._adapter.convert_to_dto(action_result.image),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def purge(
        self,
        body: BodyParam[PurgeImageRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Purge (hard-delete) an image."""
        log.info("PURGE (ak:{})", ctx.access_key)
        action_result = await self._image.purge_image_by_id.wait_for_complete(
            PurgeImageByIdAction(image_id=ImageID(body.parsed.image_id))
        )
        resp = PurgeImageResponse(
            item=self._adapter.convert_to_dto(action_result.image),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)
