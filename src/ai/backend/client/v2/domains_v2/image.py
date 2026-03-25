"""V2 REST SDK client for the image domain."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.image.request import (
    AdminSearchImageAliasesInput,
    AdminSearchImagesInput,
    AliasImageInput,
    DealiasImageInput,
    ForgetImageInput,
    PurgeImageInput,
    UpdateImageInput,
)
from ai.backend.common.dto.manager.v2.image.response import (
    AdminSearchImageAliasesPayload,
    AdminSearchImagesPayload,
    AliasImagePayload,
    ForgetImagePayload,
    PurgeImagePayload,
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

    async def admin_forget(self, request: ForgetImageInput) -> ForgetImagePayload:
        """Forget (soft-delete) an image."""
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
        """Update an image by ID (superadmin only)."""
        return await self._client.typed_request(
            "PATCH",
            _PATH,
            request=request,
            response_model=UpdateImagePayload,
        )
