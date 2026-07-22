"""V2 SDK client for the app config allow-list domain."""

from __future__ import annotations

from typing import Final
from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.app_config_allow_list.request import (
    CreateAppConfigAllowListInput,
    SearchAppConfigAllowListInput,
    UpdateAppConfigAllowListInput,
)
from ai.backend.common.dto.manager.v2.app_config_allow_list.response import (
    AppConfigAllowListNode,
    CreateAppConfigAllowListPayload,
    PurgeAppConfigAllowListPayload,
    SearchAppConfigAllowListPayload,
    UpdateAppConfigAllowListPayload,
)

_PATH: Final = "/v2/app-config-allow-lists"


class V2AppConfigAllowListClient(BaseDomainClient):
    """SDK client for app config allow-list operations.

    Mirrors the REST v2 surface introduced in BA-6546. All calls require
    super-admin privileges; the entity supports create, get, search, update
    (rank only), and purge.
    """

    async def admin_create(
        self,
        request: CreateAppConfigAllowListInput,
    ) -> CreateAppConfigAllowListPayload:
        """Register a new app config allow-list entry (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/",
            request=request,
            response_model=CreateAppConfigAllowListPayload,
        )

    async def admin_search(
        self,
        request: SearchAppConfigAllowListInput,
    ) -> SearchAppConfigAllowListPayload:
        """Search app config allow-list entries with filter/order/pagination (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=SearchAppConfigAllowListPayload,
        )

    async def admin_get(self, app_config_allow_list_id: UUID) -> AppConfigAllowListNode:
        """Get a single app config allow-list entry by ID (superadmin only)."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{app_config_allow_list_id}",
            response_model=AppConfigAllowListNode,
        )

    async def admin_update(
        self,
        app_config_allow_list_id: UUID,
        request: UpdateAppConfigAllowListInput,
    ) -> UpdateAppConfigAllowListPayload:
        """Update an app config allow-list entry's rank by ID (superadmin only)."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{app_config_allow_list_id}",
            request=request,
            response_model=UpdateAppConfigAllowListPayload,
        )

    async def admin_purge(
        self,
        app_config_allow_list_id: UUID,
    ) -> PurgeAppConfigAllowListPayload:
        """Purge an app config allow-list entry by ID (superadmin only)."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{app_config_allow_list_id}",
            response_model=PurgeAppConfigAllowListPayload,
        )
