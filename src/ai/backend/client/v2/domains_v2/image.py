"""V2 REST SDK client for the image domain."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.image.request import (
    AdminSearchImageAliasesInput,
    AdminSearchImagesInput,
)
from ai.backend.common.dto.manager.v2.image.response import (
    AdminSearchImageAliasesPayload,
    AdminSearchImagesPayload,
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
