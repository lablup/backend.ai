from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.runtime_variant.request import (
    CreateRuntimeVariantInput,
    DeleteRuntimeVariantsInput,
    SearchRuntimeVariantsInput,
    UpdateRuntimeVariantInput,
)
from ai.backend.common.dto.manager.v2.runtime_variant.response import (
    CreateRuntimeVariantPayload,
    DeleteRuntimeVariantPayload,
    DeleteRuntimeVariantsPayload,
    RuntimeVariantNode,
    SearchRuntimeVariantsPayload,
    UpdateRuntimeVariantPayload,
)

_PATH = "/v2/runtime-variants"


class V2RuntimeVariantClient(BaseDomainClient):
    async def search(self, request: SearchRuntimeVariantsInput) -> SearchRuntimeVariantsPayload:
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=SearchRuntimeVariantsPayload,
        )

    async def get(self, variant_id: UUID) -> RuntimeVariantNode:
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{variant_id}",
            response_model=RuntimeVariantNode,
        )

    async def create(self, request: CreateRuntimeVariantInput) -> CreateRuntimeVariantPayload:
        return await self._client.typed_request(
            "POST",
            _PATH,
            request=request,
            response_model=CreateRuntimeVariantPayload,
        )

    async def update(
        self, variant_id: UUID, request: UpdateRuntimeVariantInput
    ) -> UpdateRuntimeVariantPayload:
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{variant_id}",
            request=request,
            response_model=UpdateRuntimeVariantPayload,
        )

    async def delete(self, variant_id: UUID) -> DeleteRuntimeVariantPayload:
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{variant_id}",
            response_model=DeleteRuntimeVariantPayload,
        )

    async def bulk_delete(
        self, request: DeleteRuntimeVariantsInput
    ) -> DeleteRuntimeVariantsPayload:
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/delete",
            request=request,
            response_model=DeleteRuntimeVariantsPayload,
        )
