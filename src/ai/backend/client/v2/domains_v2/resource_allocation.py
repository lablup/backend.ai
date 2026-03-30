"""V2 SDK client for the resource allocation domain."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.resource_allocation.request import (
    AdminEffectiveResourceAllocationInput,
    CheckPresetAvailabilityInput,
    EffectiveResourceAllocationInput,
)
from ai.backend.common.dto.manager.v2.resource_allocation.response import (
    CheckPresetAvailabilityPayload,
    DomainResourceAllocationPayload,
    EffectiveResourceAllocationPayload,
    KeypairResourceAllocationPayload,
    ProjectResourceAllocationPayload,
    ResourceGroupResourceAllocationPayload,
)

_PATH = "/v2/resource-allocation"


class V2ResourceAllocationClient(BaseDomainClient):
    """SDK client for resource allocation operations."""

    async def my_keypair_usage(self) -> KeypairResourceAllocationPayload:
        """Get keypair resource usage for the current user."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/keypair/my",
            response_model=KeypairResourceAllocationPayload,
        )

    async def project_usage(self, project_id: UUID) -> ProjectResourceAllocationPayload:
        """Get project resource usage."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/projects/{project_id}",
            response_model=ProjectResourceAllocationPayload,
        )

    async def admin_domain_usage(self, domain_name: str) -> DomainResourceAllocationPayload:
        """Get domain resource usage (admin only)."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/domains/{domain_name}",
            response_model=DomainResourceAllocationPayload,
        )

    async def resource_group_usage(self, rg_name: str) -> ResourceGroupResourceAllocationPayload:
        """Get resource group usage."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/resource-groups/{rg_name}",
            response_model=ResourceGroupResourceAllocationPayload,
        )

    async def effective(
        self, request: EffectiveResourceAllocationInput
    ) -> EffectiveResourceAllocationPayload:
        """Get effective assignable resources for the current user."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/effective",
            request=request,
            response_model=EffectiveResourceAllocationPayload,
        )

    async def admin_effective(
        self, request: AdminEffectiveResourceAllocationInput
    ) -> EffectiveResourceAllocationPayload:
        """Get effective assignable resources for a specific user (admin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/admin/effective",
            request=request,
            response_model=EffectiveResourceAllocationPayload,
        )

    async def check_availability(
        self, request: CheckPresetAvailabilityInput
    ) -> CheckPresetAvailabilityPayload:
        """Check which resource presets are available for session creation."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/check-preset-availability",
            request=request,
            response_model=CheckPresetAvailabilityPayload,
        )
