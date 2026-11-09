from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.runtime_variant.request import (
    CreateRuntimeVariantInput,
    DeleteRuntimeVariantsInput,
    PartialBulkPurgeRuntimeVariantsInput,
    PartialBulkUpdateRuntimeVariantsInput,
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

    async def purge(self, variant_id: UUID) -> DeleteRuntimeVariantPayload:
        """Purge a runtime variant with the presets in its catalog."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{variant_id}",
            response_model=DeleteRuntimeVariantPayload,
        )

    async def partial_bulk_update(
        self, request: PartialBulkUpdateRuntimeVariantsInput
    ) -> PartialBulkPayload[RuntimeVariantNode]:
        """Update several runtime variants, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/partial-bulk-update",
            request=request,
            response_model=PartialBulkPayload[RuntimeVariantNode],
        )

    async def partial_bulk_purge(
        self, request: PartialBulkPurgeRuntimeVariantsInput
    ) -> PartialBulkPayload[RuntimeVariantNode]:
        """Purge several runtime variants with their presets, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/partial-bulk-purge",
            request=request,
            response_model=PartialBulkPayload[RuntimeVariantNode],
        )

    async def delete(self, variant_id: UUID) -> DeleteRuntimeVariantPayload:
        """Deprecated. Use :meth:`purge`."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{variant_id}",
            response_model=DeleteRuntimeVariantPayload,
        )

    async def bulk_delete(
        self, request: DeleteRuntimeVariantsInput
    ) -> DeleteRuntimeVariantsPayload:
        """Deprecated. Use :meth:`partial_bulk_purge`."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/delete",
            request=request,
            response_model=DeleteRuntimeVariantsPayload,
        )
