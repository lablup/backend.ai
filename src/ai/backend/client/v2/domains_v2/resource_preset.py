"""V2 SDK client for the resource preset domain."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.resource_allocation.request import (
    CheckPresetAvailabilityInput,
)
from ai.backend.common.dto.manager.v2.resource_allocation.response import (
    CheckPresetAvailabilityPayload,
)
from ai.backend.common.dto.manager.v2.resource_preset.request import (
    AdminSearchResourcePresetsInput,
    CreateResourcePresetInput,
    UpdateResourcePresetInput,
)
from ai.backend.common.dto.manager.v2.resource_preset.response import (
    AdminSearchResourcePresetsPayload,
    CreateResourcePresetPayload,
    DeleteResourcePresetPayload,
    ResourcePresetNode,
    UpdateResourcePresetPayload,
)

_PATH = "/v2/resource-presets"


class V2ResourcePresetClient(BaseDomainClient):
    """SDK client for resource preset management."""

    async def search(
        self, request: AdminSearchResourcePresetsInput
    ) -> AdminSearchResourcePresetsPayload:
        """Search resource presets with filters, orders, and pagination."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchResourcePresetsPayload,
        )

    async def create(self, request: CreateResourcePresetInput) -> CreateResourcePresetPayload:
        """Create a new resource preset."""
        return await self._client.typed_request(
            "POST",
            _PATH,
            request=request,
            response_model=CreateResourcePresetPayload,
        )

    async def get(self, preset_id: UUID) -> ResourcePresetNode:
        """Retrieve a single resource preset by ID."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{preset_id}",
            response_model=ResourcePresetNode,
        )

    async def update(
        self, preset_id: UUID, request: UpdateResourcePresetInput
    ) -> UpdateResourcePresetPayload:
        """Update an existing resource preset."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{preset_id}",
            request=request,
            response_model=UpdateResourcePresetPayload,
        )

    async def delete(self, preset_id: UUID) -> DeleteResourcePresetPayload:
        """Delete a resource preset by ID."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{preset_id}",
            response_model=DeleteResourcePresetPayload,
        )

    async def check_availability(
        self, request: CheckPresetAvailabilityInput
    ) -> CheckPresetAvailabilityPayload:
        """Check which resource presets are available for session creation."""
        return await self._client.typed_request(
            "POST",
            "/v2/resource-allocation/check-preset-availability",
            request=request,
            response_model=CheckPresetAvailabilityPayload,
        )
