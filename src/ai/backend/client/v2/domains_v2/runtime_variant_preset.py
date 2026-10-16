from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.runtime_variant_preset.request import (
    CreateRuntimeVariantPresetInput,
    PartialBulkPurgeRuntimeVariantPresetsInput,
    PartialBulkUpdateRuntimeVariantPresetsInput,
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

    async def purge(self, preset_id: UUID) -> DeleteRuntimeVariantPresetPayload:
        """Purge a runtime variant preset."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{preset_id}",
            response_model=DeleteRuntimeVariantPresetPayload,
        )

    async def partial_bulk_update(
        self, request: PartialBulkUpdateRuntimeVariantPresetsInput
    ) -> PartialBulkPayload[RuntimeVariantPresetNode]:
        """Update several runtime variant presets, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/partial-bulk-update",
            request=request,
            response_model=PartialBulkPayload[RuntimeVariantPresetNode],
        )

    async def partial_bulk_purge(
        self, request: PartialBulkPurgeRuntimeVariantPresetsInput
    ) -> PartialBulkPayload[RuntimeVariantPresetNode]:
        """Purge several runtime variant presets, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/partial-bulk-purge",
            request=request,
            response_model=PartialBulkPayload[RuntimeVariantPresetNode],
        )

    async def delete(self, preset_id: UUID) -> DeleteRuntimeVariantPresetPayload:
        """Deprecated. Use :meth:`purge`."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{preset_id}",
            response_model=DeleteRuntimeVariantPresetPayload,
        )
