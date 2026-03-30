from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.image.request import (
    AliasImageRequest,
    DealiasImageRequest,
    ForgetImageRequest,
    PurgeImageRequest,
    RescanImagesRequest,
    SearchImagesRequest,
)
from ai.backend.common.dto.manager.image.response import (
    AliasImageResponse,
    ForgetImageResponse,
    GetImageResponse,
    PurgeImageResponse,
    RescanImagesResponse,
    SearchImagesResponse,
)

API_PREFIX = "/admin/images"


class ImageClient(BaseDomainClient):
    """Client for image management endpoints."""

    async def search(
        self,
        request: SearchImagesRequest,
    ) -> SearchImagesResponse:
        return await self._client.typed_request(
            "POST",
            f"{API_PREFIX}/search",
            request=request,
            response_model=SearchImagesResponse,
        )

    async def get(
        self,
        image_id: UUID,
    ) -> GetImageResponse:
        return await self._client.typed_request(
            "GET",
            f"{API_PREFIX}/{image_id}",
            response_model=GetImageResponse,
        )

    async def rescan(
        self,
        request: RescanImagesRequest,
    ) -> RescanImagesResponse:
        return await self._client.typed_request(
            "POST",
            f"{API_PREFIX}/rescan",
            request=request,
            response_model=RescanImagesResponse,
        )

    async def alias(
        self,
        request: AliasImageRequest,
    ) -> AliasImageResponse:
        return await self._client.typed_request(
            "POST",
            f"{API_PREFIX}/alias",
            request=request,
            response_model=AliasImageResponse,
        )

    async def dealias(
        self,
        request: DealiasImageRequest,
    ) -> AliasImageResponse:
        return await self._client.typed_request(
            "POST",
            f"{API_PREFIX}/dealias",
            request=request,
            response_model=AliasImageResponse,
        )

    async def forget(
        self,
        request: ForgetImageRequest,
    ) -> ForgetImageResponse:
        return await self._client.typed_request(
            "POST",
            f"{API_PREFIX}/forget",
            request=request,
            response_model=ForgetImageResponse,
        )

    async def purge(
        self,
        request: PurgeImageRequest,
    ) -> PurgeImageResponse:
        return await self._client.typed_request(
            "POST",
            f"{API_PREFIX}/purge",
            request=request,
            response_model=PurgeImageResponse,
        )
