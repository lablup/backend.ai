from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.runtime_variant_preset.request import (
    CreateRuntimeVariantPresetInput,
    SearchRuntimeVariantPresetsInput,
    UpdateRuntimeVariantPresetInput,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.response import (
    CreateRuntimeVariantPresetPayload,
    DeleteRuntimeVariantPresetPayload,
    RuntimeVariantPresetNode,
    SearchRuntimeVariantPresetsPayload,
    UpdateRuntimeVariantPresetPayload,
)

_PATH = "/v2/runtime-variant-presets"


class V2RuntimeVariantPresetClient(BaseDomainClient):
    async def search(
        self, request: SearchRuntimeVariantPresetsInput
    ) -> SearchRuntimeVariantPresetsPayload:
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=SearchRuntimeVariantPresetsPayload,
        )

    async def get(self, preset_id: UUID) -> RuntimeVariantPresetNode:
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{preset_id}",
            response_model=RuntimeVariantPresetNode,
        )

    async def create(
        self, request: CreateRuntimeVariantPresetInput
    ) -> CreateRuntimeVariantPresetPayload:
        return await self._client.typed_request(
            "POST",
            _PATH,
            request=request,
            response_model=CreateRuntimeVariantPresetPayload,
        )

    async def update(
        self, preset_id: UUID, request: UpdateRuntimeVariantPresetInput
    ) -> UpdateRuntimeVariantPresetPayload:
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{preset_id}",
            request=request,
            response_model=UpdateRuntimeVariantPresetPayload,
        )

    async def delete(self, preset_id: UUID) -> DeleteRuntimeVariantPresetPayload:
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{preset_id}",
            response_model=DeleteRuntimeVariantPresetPayload,
        )
