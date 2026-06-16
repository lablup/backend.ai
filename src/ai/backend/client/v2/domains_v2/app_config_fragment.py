"""V2 SDK client for the app-config fragment domain.

Fragments are an admin-only surface — end users interact with the merged
``AppConfig`` view (``V2AppConfigClient``) instead. Self-service
``my_bulk_*`` writes that return the recomputed merged view also live on
``V2AppConfigClient`` alongside the merged-view reads.
"""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AdminBulkCreateAppConfigFragmentsInput,
    AdminBulkPurgeAppConfigFragmentsInput,
    AdminBulkUpdateAppConfigFragmentsInput,
    SearchAppConfigFragmentsInput,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    AdminBulkCreateAppConfigFragmentsPayload,
    AdminBulkPurgeAppConfigFragmentsPayload,
    AdminBulkUpdateAppConfigFragmentsPayload,
    SearchAppConfigFragmentsPayload,
)

_PATH = "/v2/app-config-fragments"


class V2AppConfigFragmentClient(BaseDomainClient):
    """SDK client for AppConfigFragment admin operations.

    Writes are bulk-only.
    """

    async def admin_search(
        self, request: SearchAppConfigFragmentsInput
    ) -> SearchAppConfigFragmentsPayload:
        """Cross-scope admin search."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=SearchAppConfigFragmentsPayload,
        )

    async def admin_bulk_create(
        self, request: AdminBulkCreateAppConfigFragmentsInput
    ) -> AdminBulkCreateAppConfigFragmentsPayload:
        """Bulk-create fragments (admin only, partial-success semantics)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/bulk-create",
            request=request,
            response_model=AdminBulkCreateAppConfigFragmentsPayload,
        )

    async def admin_bulk_update(
        self, request: AdminBulkUpdateAppConfigFragmentsInput
    ) -> AdminBulkUpdateAppConfigFragmentsPayload:
        """Bulk-update fragments (admin only, partial-success semantics)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/bulk-update",
            request=request,
            response_model=AdminBulkUpdateAppConfigFragmentsPayload,
        )

    async def admin_bulk_purge(
        self, request: AdminBulkPurgeAppConfigFragmentsInput
    ) -> AdminBulkPurgeAppConfigFragmentsPayload:
        """Bulk-purge fragments (admin only, partial-success semantics)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/bulk-purge",
            request=request,
            response_model=AdminBulkPurgeAppConfigFragmentsPayload,
        )
