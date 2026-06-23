"""V2 SDK client for the app config definition domain."""

from __future__ import annotations

from typing import Final
from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.app_config_definition.request import (
    CreateAppConfigDefinitionInput,
    SearchAppConfigDefinitionsInput,
)
from ai.backend.common.dto.manager.v2.app_config_definition.response import (
    AppConfigDefinitionNode,
    CreateAppConfigDefinitionPayload,
    PurgeAppConfigDefinitionPayload,
    SearchAppConfigDefinitionsPayload,
)

_PATH: Final = "/v2/app-config-definitions"


class V2AppConfigDefinitionClient(BaseDomainClient):
    """SDK client for app config definition operations.

    Mirrors the REST v2 surface introduced in BA-6530. All calls require
    super-admin privileges; the entity supports create, get, search, and
    purge (no update or delete).
    """

    async def admin_create(
        self,
        request: CreateAppConfigDefinitionInput,
    ) -> CreateAppConfigDefinitionPayload:
        """Register a new app config definition (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/",
            request=request,
            response_model=CreateAppConfigDefinitionPayload,
        )

    async def admin_search(
        self,
        request: SearchAppConfigDefinitionsInput,
    ) -> SearchAppConfigDefinitionsPayload:
        """Search app config definitions with filter/order/pagination (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=SearchAppConfigDefinitionsPayload,
        )

    async def admin_get(self, app_config_definition_id: UUID) -> AppConfigDefinitionNode:
        """Get a single app config definition by ID (superadmin only)."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{app_config_definition_id}",
            response_model=AppConfigDefinitionNode,
        )

    async def admin_purge(
        self,
        app_config_definition_id: UUID,
    ) -> PurgeAppConfigDefinitionPayload:
        """Purge an app config definition by ID (superadmin only)."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{app_config_definition_id}",
            response_model=PurgeAppConfigDefinitionPayload,
        )
