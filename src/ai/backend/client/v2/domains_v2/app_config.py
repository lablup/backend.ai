"""V2 SDK client for the merged AppConfig view.

Replaces the legacy upsert-style domain/user app-config SDK; the new
surface is bulk-only writes against `USER`-scope fragments plus
merged-view reads.
"""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.app_config.request import (
    ScopedSearchAppConfigsInput,
    SearchAppConfigsInput,
)
from ai.backend.common.dto.manager.v2.app_config.response import (
    GetUserAppConfigPayload,
    MyBulkCreateAppConfigFragmentsPayload,
    MyBulkUpdateAppConfigFragmentsPayload,
    SearchAppConfigsPayload,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    MyBulkCreateAppConfigFragmentsInput,
    MyBulkUpdateAppConfigFragmentsInput,
)

_PATH = "/v2/app-configs"
_FRAGMENT_PATH = "/v2/app-config-fragments"


class V2AppConfigClient(BaseDomainClient):
    """SDK client for the merged AppConfig view + self-service writes."""

    async def scoped_search(
        self, request: ScopedSearchAppConfigsInput
    ) -> SearchAppConfigsPayload:
        """Scoped merged-view search; `scope.user_ids` are OR'd and
        RBAC-gated. Self-service is a USER-scoped search over the caller's
        own id."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/scoped/search",
            request=request,
            response_model=SearchAppConfigsPayload,
        )

    async def admin_get(self, user_id: UUID, name: str) -> GetUserAppConfigPayload:
        """Read a specific user's merged AppConfig (admin only)."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{user_id}/{name}",
            response_model=GetUserAppConfigPayload,
        )

    async def admin_search(self, request: SearchAppConfigsInput) -> SearchAppConfigsPayload:
        """Cross-user merged-view search (admin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=SearchAppConfigsPayload,
        )

    async def my_bulk_create(
        self, request: MyBulkCreateAppConfigFragmentsInput
    ) -> MyBulkCreateAppConfigFragmentsPayload:
        """Bulk-create USER-scope fragments; returns recomputed merged views."""
        return await self._client.typed_request(
            "POST",
            f"{_FRAGMENT_PATH}/my/bulk-create",
            request=request,
            response_model=MyBulkCreateAppConfigFragmentsPayload,
        )

    async def my_bulk_update(
        self, request: MyBulkUpdateAppConfigFragmentsInput
    ) -> MyBulkUpdateAppConfigFragmentsPayload:
        """Bulk-update USER-scope fragments; returns recomputed merged views."""
        return await self._client.typed_request(
            "POST",
            f"{_FRAGMENT_PATH}/my/bulk-update",
            request=request,
            response_model=MyBulkUpdateAppConfigFragmentsPayload,
        )
