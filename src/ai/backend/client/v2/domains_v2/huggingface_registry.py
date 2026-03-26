"""V2 REST SDK client for the HuggingFace registry resource."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.huggingface_registry.request import (
    AdminSearchHuggingFaceRegistriesInput,
    CreateHuggingFaceRegistryInput,
    DeleteHuggingFaceRegistryInput,
    UpdateHuggingFaceRegistryInput,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.response import (
    AdminSearchHuggingFaceRegistriesPayload,
    CreateHuggingFaceRegistryPayload,
    DeleteHuggingFaceRegistryPayload,
    HuggingFaceRegistryNode,
    UpdateHuggingFaceRegistryPayload,
)

_PATH = "/v2/huggingface-registries"


class V2HuggingFaceRegistryClient(BaseDomainClient):
    """SDK client for ``/v2/huggingface-registries`` endpoints."""

    async def create(
        self,
        request: CreateHuggingFaceRegistryInput,
    ) -> CreateHuggingFaceRegistryPayload:
        """Create a new HuggingFace registry."""
        return await self._client.typed_request(
            "POST",
            _PATH,
            request=request,
            response_model=CreateHuggingFaceRegistryPayload,
        )

    async def search(
        self,
        request: AdminSearchHuggingFaceRegistriesInput,
    ) -> AdminSearchHuggingFaceRegistriesPayload:
        """Search HuggingFace registries with pagination."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchHuggingFaceRegistriesPayload,
        )

    async def get(self, registry_id: UUID) -> HuggingFaceRegistryNode:
        """Get a single HuggingFace registry by ID."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{registry_id}",
            response_model=HuggingFaceRegistryNode,
        )

    async def update(
        self,
        request: UpdateHuggingFaceRegistryInput,
    ) -> UpdateHuggingFaceRegistryPayload:
        """Update an existing HuggingFace registry."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{request.id}",
            request=request,
            response_model=UpdateHuggingFaceRegistryPayload,
        )

    async def delete(
        self,
        request: DeleteHuggingFaceRegistryInput,
    ) -> DeleteHuggingFaceRegistryPayload:
        """Delete a HuggingFace registry."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/delete",
            request=request,
            response_model=DeleteHuggingFaceRegistryPayload,
        )
