"""V2 REST SDK client for the resource policy resource."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    AdminSearchKeypairResourcePoliciesInput,
    AdminSearchProjectResourcePoliciesInput,
    AdminSearchUserResourcePoliciesInput,
    CreateKeypairResourcePolicyInput,
    CreateProjectResourcePolicyInput,
    CreateUserResourcePolicyInput,
    UpdateKeypairResourcePolicyInput,
    UpdateProjectResourcePolicyInput,
    UpdateUserResourcePolicyInput,
)
from ai.backend.common.dto.manager.v2.resource_policy.response import (
    CreateKeypairResourcePolicyPayload,
    CreateProjectResourcePolicyPayload,
    CreateUserResourcePolicyPayload,
    DeleteKeypairResourcePolicyPayload,
    DeleteProjectResourcePolicyPayload,
    DeleteUserResourcePolicyPayload,
    KeypairResourcePolicyNode,
    ProjectResourcePolicyNode,
    SearchKeypairResourcePoliciesPayload,
    SearchProjectResourcePoliciesPayload,
    SearchUserResourcePoliciesPayload,
    UpdateKeypairResourcePolicyPayload,
    UpdateProjectResourcePolicyPayload,
    UpdateUserResourcePolicyPayload,
    UserResourcePolicyNode,
)

_KEYPAIR_PATH = "/v2/resource-policies/keypair"
_USER_PATH = "/v2/resource-policies/user"
_PROJECT_PATH = "/v2/resource-policies/project"


class V2ResourcePolicyClient(BaseDomainClient):
    """SDK client for ``/v2/resource-policies`` endpoints."""

    # ── Keypair Resource Policy ──

    async def admin_search_keypair_resource_policies(
        self, request: AdminSearchKeypairResourcePoliciesInput
    ) -> SearchKeypairResourcePoliciesPayload:
        return await self._client.typed_request(
            "POST",
            f"{_KEYPAIR_PATH}/search",
            request=request,
            response_model=SearchKeypairResourcePoliciesPayload,
        )

    async def admin_get_keypair_resource_policy(self, name: str) -> KeypairResourcePolicyNode:
        return await self._client.typed_request(
            "GET",
            f"{_KEYPAIR_PATH}/{name}",
            response_model=KeypairResourcePolicyNode,
        )

    async def admin_create_keypair_resource_policy(
        self, request: CreateKeypairResourcePolicyInput
    ) -> CreateKeypairResourcePolicyPayload:
        return await self._client.typed_request(
            "POST",
            _KEYPAIR_PATH,
            request=request,
            response_model=CreateKeypairResourcePolicyPayload,
        )

    async def admin_update_keypair_resource_policy(
        self, name: str, request: UpdateKeypairResourcePolicyInput
    ) -> UpdateKeypairResourcePolicyPayload:
        return await self._client.typed_request(
            "PATCH",
            f"{_KEYPAIR_PATH}/{name}",
            request=request,
            response_model=UpdateKeypairResourcePolicyPayload,
        )

    async def admin_delete_keypair_resource_policy(
        self, name: str
    ) -> DeleteKeypairResourcePolicyPayload:
        return await self._client.typed_request(
            "DELETE",
            f"{_KEYPAIR_PATH}/{name}",
            response_model=DeleteKeypairResourcePolicyPayload,
        )

    async def get_my_keypair_resource_policy(self) -> KeypairResourcePolicyNode:
        return await self._client.typed_request(
            "GET",
            f"{_KEYPAIR_PATH}/my",
            response_model=KeypairResourcePolicyNode,
        )

    # ── User Resource Policy ──

    async def admin_search_user_resource_policies(
        self, request: AdminSearchUserResourcePoliciesInput
    ) -> SearchUserResourcePoliciesPayload:
        return await self._client.typed_request(
            "POST",
            f"{_USER_PATH}/search",
            request=request,
            response_model=SearchUserResourcePoliciesPayload,
        )

    async def admin_get_user_resource_policy(self, name: str) -> UserResourcePolicyNode:
        return await self._client.typed_request(
            "GET",
            f"{_USER_PATH}/{name}",
            response_model=UserResourcePolicyNode,
        )

    async def admin_create_user_resource_policy(
        self, request: CreateUserResourcePolicyInput
    ) -> CreateUserResourcePolicyPayload:
        return await self._client.typed_request(
            "POST",
            _USER_PATH,
            request=request,
            response_model=CreateUserResourcePolicyPayload,
        )

    async def admin_update_user_resource_policy(
        self, name: str, request: UpdateUserResourcePolicyInput
    ) -> UpdateUserResourcePolicyPayload:
        return await self._client.typed_request(
            "PATCH",
            f"{_USER_PATH}/{name}",
            request=request,
            response_model=UpdateUserResourcePolicyPayload,
        )

    async def admin_delete_user_resource_policy(self, name: str) -> DeleteUserResourcePolicyPayload:
        return await self._client.typed_request(
            "DELETE",
            f"{_USER_PATH}/{name}",
            response_model=DeleteUserResourcePolicyPayload,
        )

    async def get_my_user_resource_policy(self) -> UserResourcePolicyNode:
        return await self._client.typed_request(
            "GET",
            f"{_USER_PATH}/my",
            response_model=UserResourcePolicyNode,
        )

    # ── Project Resource Policy ──

    async def admin_search_project_resource_policies(
        self, request: AdminSearchProjectResourcePoliciesInput
    ) -> SearchProjectResourcePoliciesPayload:
        return await self._client.typed_request(
            "POST",
            f"{_PROJECT_PATH}/search",
            request=request,
            response_model=SearchProjectResourcePoliciesPayload,
        )

    async def admin_get_project_resource_policy(self, name: str) -> ProjectResourcePolicyNode:
        return await self._client.typed_request(
            "GET",
            f"{_PROJECT_PATH}/{name}",
            response_model=ProjectResourcePolicyNode,
        )

    async def admin_create_project_resource_policy(
        self, request: CreateProjectResourcePolicyInput
    ) -> CreateProjectResourcePolicyPayload:
        return await self._client.typed_request(
            "POST",
            _PROJECT_PATH,
            request=request,
            response_model=CreateProjectResourcePolicyPayload,
        )

    async def admin_update_project_resource_policy(
        self, name: str, request: UpdateProjectResourcePolicyInput
    ) -> UpdateProjectResourcePolicyPayload:
        return await self._client.typed_request(
            "PATCH",
            f"{_PROJECT_PATH}/{name}",
            request=request,
            response_model=UpdateProjectResourcePolicyPayload,
        )

    async def admin_delete_project_resource_policy(
        self, name: str
    ) -> DeleteProjectResourcePolicyPayload:
        return await self._client.typed_request(
            "DELETE",
            f"{_PROJECT_PATH}/{name}",
            response_model=DeleteProjectResourcePolicyPayload,
        )
