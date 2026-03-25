"""V2 REST SDK client for the project resource."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.group.request import (
    AdminSearchGroupsInput,
)
from ai.backend.common.dto.manager.v2.group.response import (
    AdminSearchGroupsPayload,
    ProjectNode,
)

_PATH = "/v2/projects"


class V2ProjectClient(BaseDomainClient):
    """SDK client for ``/v2/projects`` endpoints."""

    async def admin_search(
        self,
        request: AdminSearchGroupsInput,
    ) -> AdminSearchGroupsPayload:
        """Search projects with filters, orders, and pagination (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchGroupsPayload,
        )

    async def get(self, project_id: UUID) -> ProjectNode:
        """Retrieve a single project by UUID."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{project_id}",
            response_model=ProjectNode,
        )
