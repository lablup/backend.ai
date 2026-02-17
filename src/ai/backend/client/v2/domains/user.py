from __future__ import annotations

import uuid

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.user import (
    CreateUserRequest,
    CreateUserResponse,
    DeleteUserRequest,
    DeleteUserResponse,
    GetUserResponse,
    PurgeUserRequest,
    PurgeUserResponse,
    SearchUsersRequest,
    SearchUsersResponse,
    UpdateUserRequest,
    UpdateUserResponse,
)

_USERS_PATH = "/admin/users"


class UserClient(BaseDomainClient):
    async def create(
        self,
        request: CreateUserRequest,
    ) -> CreateUserResponse:
        return await self._client.typed_request(
            "POST",
            _USERS_PATH,
            request=request,
            response_model=CreateUserResponse,
        )

    async def get(
        self,
        user_id: uuid.UUID,
    ) -> GetUserResponse:
        return await self._client.typed_request(
            "GET",
            f"{_USERS_PATH}/{user_id}",
            response_model=GetUserResponse,
        )

    async def search(
        self,
        request: SearchUsersRequest,
    ) -> SearchUsersResponse:
        return await self._client.typed_request(
            "POST",
            f"{_USERS_PATH}/search",
            request=request,
            response_model=SearchUsersResponse,
        )

    async def update(
        self,
        user_id: uuid.UUID,
        request: UpdateUserRequest,
    ) -> UpdateUserResponse:
        return await self._client.typed_request(
            "PATCH",
            f"{_USERS_PATH}/{user_id}",
            request=request,
            response_model=UpdateUserResponse,
        )

    async def delete(
        self,
        request: DeleteUserRequest,
    ) -> DeleteUserResponse:
        return await self._client.typed_request(
            "POST",
            f"{_USERS_PATH}/delete",
            request=request,
            response_model=DeleteUserResponse,
        )

    async def purge(
        self,
        request: PurgeUserRequest,
    ) -> PurgeUserResponse:
        return await self._client.typed_request(
            "POST",
            f"{_USERS_PATH}/purge",
            request=request,
            response_model=PurgeUserResponse,
        )
