"""V2 REST SDK client for the project resource."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.group.request import (
    AdminSearchGroupsInput,
    CreateGroupInput,
    DeleteGroupInput,
    PurgeGroupInput,
    UpdateGroupInput,
)
from ai.backend.common.dto.manager.v2.group.response import (
    AdminSearchGroupsPayload,
    DeleteProjectPayload,
    ProjectNode,
    ProjectPayload,
    PurgeProjectPayload,
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

    async def admin_create(self, request: CreateGroupInput) -> ProjectPayload:
        """Create a new project (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            _PATH,
            request=request,
            response_model=ProjectPayload,
        )

    async def admin_update(self, project_id: UUID, request: UpdateGroupInput) -> ProjectPayload:
        """Update a project (superadmin only)."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{project_id}",
            request=request,
            response_model=ProjectPayload,
        )

    async def admin_delete(self, request: DeleteGroupInput) -> DeleteProjectPayload:
        """Soft-delete a project (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/delete",
            request=request,
            response_model=DeleteProjectPayload,
        )

    async def admin_purge(self, request: PurgeGroupInput) -> PurgeProjectPayload:
        """Permanently purge a project (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/purge",
            request=request,
            response_model=PurgeProjectPayload,
        )
