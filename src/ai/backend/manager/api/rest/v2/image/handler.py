"""REST v2 handler for the image domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.dto.manager.v2.image.request import (
    AdminSearchImageAliasesInput,
    AdminSearchImagesInput,
    AliasImageInput,
    DealiasImageInput,
    ForgetImageInput,
    PurgeImageInput,
    UpdateImageInput,
)
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.image import ImageAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2ImageHandler:
    """REST v2 handler for image operations."""

    def __init__(self, *, adapter: ImageAdapter) -> None:
        self._adapter = adapter

    async def admin_search_images(
        self,
        body: BodyParam[AdminSearchImagesInput],
    ) -> APIResponse:
        """Search images with admin scope."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search_image_aliases(
        self,
        body: BodyParam[AdminSearchImageAliasesInput],
    ) -> APIResponse:
        """Search image aliases with admin scope."""
        result = await self._adapter.admin_search_image_aliases(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_forget(self, body: BodyParam[ForgetImageInput]) -> APIResponse:
        """Forget (soft-delete) an image."""
        result = await self._adapter.admin_forget(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_purge(self, body: BodyParam[PurgeImageInput]) -> APIResponse:
        """Purge (hard-delete) an image."""
        result = await self._adapter.admin_purge(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_alias(self, body: BodyParam[AliasImageInput]) -> APIResponse:
        """Create an alias for an image."""
        result = await self._adapter.admin_alias(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def admin_dealias(self, body: BodyParam[DealiasImageInput]) -> APIResponse:
        """Remove an image alias."""
        result = await self._adapter.admin_dealias(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_update(self, body: BodyParam[UpdateImageInput]) -> APIResponse:
        """Update an image by ID."""
        result = await self._adapter.admin_update(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
