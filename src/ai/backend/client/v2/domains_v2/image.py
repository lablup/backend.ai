"""V2 REST SDK client for the image domain."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
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
    UpdateImageBody,
    UpdateImageInput,
)
from ai.backend.common.dto.manager.v2.image.response import (
    AdminSearchImageAliasesPayload,
    AdminSearchImagesPayload,
    AliasImagePayload,
    DeleteImagePayload,
    ForgetImagePayload,
    ImageNode,
    PurgeImagePayload,
    RestoreImagePayload,
    ScopedSearchImagesPayload,
    UpdateImagePayload,
)

_PATH = "/v2/images"


class V2ImageClient(BaseDomainClient):
    """SDK client for the ``/v2/images`` REST endpoints."""

    async def admin_search(
        self,
        request: AdminSearchImagesInput,
    ) -> AdminSearchImagesPayload:
        """Search images with admin scope."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchImagesPayload,
        )

    async def my_search(
        self,
        request: AdminSearchImagesInput,
    ) -> ScopedSearchImagesPayload:
        """Search the images the current user can reach."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/my/search",
            request=request,
            response_model=ScopedSearchImagesPayload,
        )

    async def admin_search_image_aliases(
        self,
        request: AdminSearchImageAliasesInput,
    ) -> AdminSearchImageAliasesPayload:
        """Search image aliases with admin scope."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/aliases/search",
            request=request,
            response_model=AdminSearchImageAliasesPayload,
        )

    async def update(self, image_id: UUID, request: UpdateImageBody) -> UpdateImagePayload:
        """Update an image."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{image_id}",
            request=request,
            response_model=UpdateImagePayload,
        )

    async def delete(self, image_id: UUID) -> DeleteImagePayload:
        """Forget (soft-delete) an image."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{image_id}/delete",
            response_model=DeleteImagePayload,
        )

    async def restore(self, image_id: UUID) -> RestoreImagePayload:
        """Restore a forgotten (soft-deleted) image."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{image_id}/restore",
            response_model=RestoreImagePayload,
        )

    async def partial_bulk_update(
        self, request: PartialBulkUpdateImagesInput
    ) -> PartialBulkPayload[ImageNode]:
        """Update several images, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/partial-bulk-update",
            request=request,
            response_model=PartialBulkPayload[ImageNode],
        )

    async def partial_bulk_delete(
        self, request: PartialBulkDeleteImagesInput
    ) -> PartialBulkPayload[ImageNode]:
        """Forget several images, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/partial-bulk-delete",
            request=request,
            response_model=PartialBulkPayload[ImageNode],
        )

    async def partial_bulk_restore(
        self, request: PartialBulkRestoreImagesInput
    ) -> PartialBulkPayload[ImageNode]:
        """Restore several forgotten images, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/partial-bulk-restore",
            request=request,
            response_model=PartialBulkPayload[ImageNode],
        )

    async def admin_forget(self, request: ForgetImageInput) -> ForgetImagePayload:
        """Deprecated. Use :meth:`delete`."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/forget",
            request=request,
            response_model=ForgetImagePayload,
        )

    async def admin_purge(self, request: PurgeImageInput) -> PurgeImagePayload:
        """Purge (hard-delete) an image."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/purge",
            request=request,
            response_model=PurgeImagePayload,
        )

    async def admin_alias(self, request: AliasImageInput) -> AliasImagePayload:
        """Create an alias for an image."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/alias",
            request=request,
            response_model=AliasImagePayload,
        )

    async def admin_dealias(self, request: DealiasImageInput) -> AliasImagePayload:
        """Remove an image alias."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/dealias",
            request=request,
            response_model=AliasImagePayload,
        )

    async def admin_update(self, request: UpdateImageInput) -> UpdateImagePayload:
        """Deprecated. Use :meth:`update`."""
        return await self._client.typed_request(
            "PATCH",
            _PATH,
            request=request,
            response_model=UpdateImagePayload,
        )
