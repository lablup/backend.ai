"""V2 SDK client for the idle checker assignment domain."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
    CreateIdleCheckerAssignmentInput,
    ScopedSearchIdleCheckerAssignmentsInput,
    SearchIdleCheckerAssignmentsInput,
    UpdateIdleCheckerAssignmentInput,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.response import (
    CreateIdleCheckerAssignmentPayload,
    PurgeIdleCheckerAssignmentPayload,
    SearchIdleCheckerAssignmentPayload,
    UpdateIdleCheckerAssignmentPayload,
)

_PATH = "/v2/idle-checker-assignments"


class V2IdleCheckerAssignmentClient(BaseDomainClient):
    """SDK client for idle checker assignment operations."""

    async def admin_create(
        self,
        request: CreateIdleCheckerAssignmentInput,
    ) -> CreateIdleCheckerAssignmentPayload:
        """Bind a global idle checker to a scope (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/",
            request=request,
            response_model=CreateIdleCheckerAssignmentPayload,
        )

    async def admin_search(
        self,
        request: SearchIdleCheckerAssignmentsInput,
    ) -> SearchIdleCheckerAssignmentPayload:
        """Search idle checker assignments across all scopes (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=SearchIdleCheckerAssignmentPayload,
        )

    async def scoped_search(
        self,
        request: ScopedSearchIdleCheckerAssignmentsInput,
    ) -> SearchIdleCheckerAssignmentPayload:
        """Search idle checker assignments within the given scopes (per-item RBAC)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/scoped/search",
            request=request,
            response_model=SearchIdleCheckerAssignmentPayload,
        )

    async def update(
        self,
        idle_checker_assignment_id: UUID,
        request: UpdateIdleCheckerAssignmentInput,
    ) -> UpdateIdleCheckerAssignmentPayload:
        """Update an idle checker assignment's enabled state by ID."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{idle_checker_assignment_id}",
            request=request,
            response_model=UpdateIdleCheckerAssignmentPayload,
        )

    async def purge(
        self,
        idle_checker_assignment_id: UUID,
    ) -> PurgeIdleCheckerAssignmentPayload:
        """Permanently remove an idle checker assignment by ID."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{idle_checker_assignment_id}",
            response_model=PurgeIdleCheckerAssignmentPayload,
        )
