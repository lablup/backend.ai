"""REST v2 handler for the image domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.dto.manager.v2.image.request import (
    AdminSearchImageAliasesInput,
    AdminSearchImagesInput,
    AliasImageInput,
    DealiasImageInput,
    ForgetImageInput,
    PartialBulkDeleteImagesInput,
    PartialBulkRestoreImagesInput,
    PartialBulkUpdateImagesInput,
    PurgeImageInput,
    RestoreImageInput,
    ScopedSearchImagesInput,
    UpdateImageBody,
    UpdateImageInput,
)
from ai.backend.common.dto.manager.v2.image.response import ForgetImagePayload
from ai.backend.common.dto.manager.v2.image.types import ImageScope
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.api.rest.v2.path_params import ImageIdPathParam
from ai.backend.manager.dto.context import UserContext

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.image.adapter import ImageAdapter

log: Final = StructuredLogger(logging.getLogger(__spec__.name))


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

    async def my_search_images(
        self,
        user_ctx: UserContext,
        body: BodyParam[AdminSearchImagesInput],
    ) -> APIResponse:
        """Search the images the current user can reach."""
        result = await self._adapter.scoped_search(
            ScopedSearchImagesInput(
                scope=ImageScope(user=[UUIDScope(value=user_ctx.user_uuid)]),
                usage=body.parsed.usage,
                filter=body.parsed.filter,
                order=body.parsed.order,
                first=body.parsed.first,
                after=body.parsed.after,
                last=body.parsed.last,
                before=body.parsed.before,
                limit=body.parsed.limit,
                offset=body.parsed.offset,
            )
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def scoped_search_images(
        self,
        body: BodyParam[ScopedSearchImagesInput],
    ) -> APIResponse:
        """Search the images the named scopes reach."""
        result = await self._adapter.scoped_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search_image_aliases(
        self,
        body: BodyParam[AdminSearchImageAliasesInput],
    ) -> APIResponse:
        """Search image aliases with admin scope."""
        result = await self._adapter.admin_search_image_aliases(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update(
        self,
        path: PathParam[ImageIdPathParam],
        body: BodyParam[UpdateImageBody],
    ) -> APIResponse:
        """Update an image."""
        result = await self._adapter.update(ImageID(path.parsed.image_id), body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete(self, path: PathParam[ImageIdPathParam]) -> APIResponse:
        """Forget (soft-delete) an image."""
        result = await self._adapter.delete(ImageID(path.parsed.image_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def restore(self, path: PathParam[ImageIdPathParam]) -> APIResponse:
        """Restore a forgotten (soft-deleted) image."""
        result = await self._adapter.restore(ImageID(path.parsed.image_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_update(
        self, body: BodyParam[PartialBulkUpdateImagesInput]
    ) -> APIResponse:
        """Update several images, answering for each one."""
        result = await self._adapter.partial_bulk_update(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_delete(
        self, body: BodyParam[PartialBulkDeleteImagesInput]
    ) -> APIResponse:
        """Forget several images, answering for each one."""
        result = await self._adapter.partial_bulk_delete(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_restore(
        self, body: BodyParam[PartialBulkRestoreImagesInput]
    ) -> APIResponse:
        """Restore several forgotten images, answering for each one."""
        result = await self._adapter.partial_bulk_restore(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_forget(self, body: BodyParam[ForgetImageInput]) -> APIResponse:
        """Deprecated. Use `POST /v2/images/{image_id}/delete`."""
        result = await self._adapter.delete(ImageID(body.parsed.image_id))
        return APIResponse.build(
            status_code=HTTPStatus.OK, response_model=ForgetImagePayload(item=result.item)
        )

    async def admin_restore(self, body: BodyParam[RestoreImageInput]) -> APIResponse:
        """Deprecated. Use `POST /v2/images/{image_id}/restore`."""
        result = await self._adapter.restore(ImageID(body.parsed.image_id))
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
        """Deprecated. Use `PATCH /v2/images/{image_id}`."""
        result = await self._adapter.update(ImageID(body.parsed.image_id), body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
