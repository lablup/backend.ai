"""V2 REST SDK client for the user resource."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.user.request import (
    CreateUserInput,
    DeleteUserInput,
    SearchUsersRequest,
    UpdateUserInput,
)
from ai.backend.common.dto.manager.v2.user.response import (
    CreateUserPayload,
    DeleteUserPayload,
    SearchUsersPayload,
    UpdateUserPayload,
    UserPayload,
)

_PATH = "/v2/users"


class V2UserClient(BaseDomainClient):
    """SDK client for ``/v2/users`` endpoints."""

    async def admin_search(
        self,
        request: SearchUsersRequest,
    ) -> SearchUsersPayload:
        """Search users with filters, orders, and pagination (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=SearchUsersPayload,
        )

    async def get(self, user_id: UUID) -> UserPayload:
        """Retrieve a single user by UUID."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{user_id}",
            response_model=UserPayload,
        )

    async def create(self, request: CreateUserInput) -> CreateUserPayload:
        """Create a new user (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            _PATH,
            request=request,
            response_model=CreateUserPayload,
        )

    async def update(
        self,
        user_id: UUID,
        request: UpdateUserInput,
    ) -> UpdateUserPayload:
        """Update a user by UUID (superadmin only)."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{user_id}",
            request=request,
            response_model=UpdateUserPayload,
        )

    async def delete(self, request: DeleteUserInput) -> DeleteUserPayload:
        """Soft-delete a user (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/delete",
            request=request,
            response_model=DeleteUserPayload,
        )

    async def search_by_domain(
        self,
        domain_name: str,
        request: SearchUsersRequest,
    ) -> SearchUsersPayload:
        """Search users scoped to a specific domain."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search-by-domain/{domain_name}",
            request=request,
            response_model=SearchUsersPayload,
        )

    async def search_by_project(
        self,
        project_id: UUID,
        request: SearchUsersRequest,
    ) -> SearchUsersPayload:
        """Search users scoped to a specific project."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search-by-project/{project_id}",
            request=request,
            response_model=SearchUsersPayload,
        )

    async def search_by_role(
        self,
        role_id: UUID,
        request: SearchUsersRequest,
    ) -> SearchUsersPayload:
        """Search users scoped to a specific role."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search-by-role/{role_id}",
            request=request,
            response_model=SearchUsersPayload,
        )
