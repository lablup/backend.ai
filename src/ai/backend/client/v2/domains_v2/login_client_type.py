"""V2 SDK client for the login client type domain."""

from __future__ import annotations

from typing import Final
from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.login_client_type.request import (
    CreateLoginClientTypeInput,
    UpdateLoginClientTypeInput,
)
from ai.backend.common.dto.manager.v2.login_client_type.response import (
    CreateLoginClientTypePayload,
    DeleteLoginClientTypePayload,
    ListLoginClientTypesPayload,
    LoginClientTypeNode,
    UpdateLoginClientTypePayload,
)

_PATH: Final = "/v2/login-client-types"


class V2LoginClientTypeClient(BaseDomainClient):
    """SDK client for login client type CRUD operations.

    Mirrors the REST v2 surface introduced in BA-5630. Mutating calls
    require super-admin privileges; the read calls are open to any
    authenticated user.
    """

    async def admin_create(
        self,
        request: CreateLoginClientTypeInput,
    ) -> CreateLoginClientTypePayload:
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/",
            request=request,
            response_model=CreateLoginClientTypePayload,
        )

    async def list_all(self) -> ListLoginClientTypesPayload:
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/",
            response_model=ListLoginClientTypesPayload,
        )

    async def get(self, login_client_type_id: UUID) -> LoginClientTypeNode:
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{login_client_type_id}",
            response_model=LoginClientTypeNode,
        )

    async def admin_update(
        self,
        login_client_type_id: UUID,
        request: UpdateLoginClientTypeInput,
    ) -> UpdateLoginClientTypePayload:
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{login_client_type_id}",
            request=request,
            response_model=UpdateLoginClientTypePayload,
        )

    async def admin_delete(
        self,
        login_client_type_id: UUID,
    ) -> DeleteLoginClientTypePayload:
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{login_client_type_id}",
            response_model=DeleteLoginClientTypePayload,
        )
