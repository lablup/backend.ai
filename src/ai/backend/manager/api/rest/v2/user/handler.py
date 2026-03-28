"""REST v2 handler for the user resource."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.user.request import (
    CreateUserInput,
    DeleteUserInput,
    SearchUsersRequest,
    UpdateUserInput,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import (
    DomainNamePathParam,
    ProjectIdPathParam,
    RoleIdPathParam,
    UserIdPathParam,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.user import UserAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2UserHandler:
    """REST v2 handler for user operations."""

    def __init__(self, *, adapter: UserAdapter) -> None:
        self._adapter = adapter

    async def admin_search(
        self,
        body: BodyParam[SearchUsersRequest],
    ) -> APIResponse:
        """Search users with filters, orders, and pagination (superadmin only)."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def get(
        self,
        path: PathParam[UserIdPathParam],
    ) -> APIResponse:
        """Retrieve a single user by UUID."""
        result = await self._adapter.get(path.parsed.user_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def create_user(
        self,
        body: BodyParam[CreateUserInput],
    ) -> APIResponse:
        """Create a new user (superadmin only)."""
        result = await self._adapter.create_user(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def modify_user(
        self,
        path: PathParam[UserIdPathParam],
        body: BodyParam[UpdateUserInput],
    ) -> APIResponse:
        """Update a user by UUID (superadmin only)."""
        result = await self._adapter.modify_user_by_id(path.parsed.user_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete_user(
        self,
        body: BodyParam[DeleteUserInput],
    ) -> APIResponse:
        """Soft-delete a user (superadmin only)."""
        result = await self._adapter.delete_user_by_id(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def domain_search(
        self,
        path: PathParam[DomainNamePathParam],
        body: BodyParam[SearchUsersRequest],
    ) -> APIResponse:
        """Search users scoped to a domain."""
        result = await self._adapter.domain_search(path.parsed.domain_name, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def project_search(
        self,
        path: PathParam[ProjectIdPathParam],
        body: BodyParam[SearchUsersRequest],
    ) -> APIResponse:
        """Search users scoped to a project."""
        result = await self._adapter.project_search(path.parsed.project_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def role_search(
        self,
        path: PathParam[RoleIdPathParam],
        body: BodyParam[SearchUsersRequest],
    ) -> APIResponse:
        """Search users scoped to a role."""
        result = await self._adapter.role_search(path.parsed.role_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
