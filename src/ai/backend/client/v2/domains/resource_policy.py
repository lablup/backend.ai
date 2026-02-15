from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.resource_policy.request import (
    CreateKeypairResourcePolicyRequest,
    CreateProjectResourcePolicyRequest,
    CreateUserResourcePolicyRequest,
    DeleteKeypairResourcePolicyRequest,
    DeleteProjectResourcePolicyRequest,
    DeleteUserResourcePolicyRequest,
    SearchKeypairResourcePoliciesRequest,
    SearchProjectResourcePoliciesRequest,
    SearchUserResourcePoliciesRequest,
    UpdateKeypairResourcePolicyRequest,
    UpdateProjectResourcePolicyRequest,
    UpdateUserResourcePolicyRequest,
)
from ai.backend.common.dto.manager.resource_policy.response import (
    CreateKeypairResourcePolicyResponse,
    CreateProjectResourcePolicyResponse,
    CreateUserResourcePolicyResponse,
    DeleteKeypairResourcePolicyResponse,
    DeleteProjectResourcePolicyResponse,
    DeleteUserResourcePolicyResponse,
    GetKeypairResourcePolicyResponse,
    GetProjectResourcePolicyResponse,
    GetUserResourcePolicyResponse,
    SearchKeypairResourcePoliciesResponse,
    SearchProjectResourcePoliciesResponse,
    SearchUserResourcePoliciesResponse,
    UpdateKeypairResourcePolicyResponse,
    UpdateProjectResourcePolicyResponse,
    UpdateUserResourcePolicyResponse,
)


class ResourcePolicyClient(BaseDomainClient):
    # ---- Keypair Resource Policy ----

    async def create_keypair_policy(
        self, request: CreateKeypairResourcePolicyRequest
    ) -> CreateKeypairResourcePolicyResponse:
        return await self._client.typed_request(
            "POST",
            "/admin/resource-policies/keypair",
            request=request,
            response_model=CreateKeypairResourcePolicyResponse,
        )

    async def get_keypair_policy(self, policy_name: str) -> GetKeypairResourcePolicyResponse:
        return await self._client.typed_request(
            "GET",
            f"/admin/resource-policies/keypair/{policy_name}",
            response_model=GetKeypairResourcePolicyResponse,
        )

    async def search_keypair_policies(
        self, request: SearchKeypairResourcePoliciesRequest
    ) -> SearchKeypairResourcePoliciesResponse:
        return await self._client.typed_request(
            "POST",
            "/admin/resource-policies/keypair/search",
            request=request,
            response_model=SearchKeypairResourcePoliciesResponse,
        )

    async def update_keypair_policy(
        self, policy_name: str, request: UpdateKeypairResourcePolicyRequest
    ) -> UpdateKeypairResourcePolicyResponse:
        return await self._client.typed_request(
            "PATCH",
            f"/admin/resource-policies/keypair/{policy_name}",
            request=request,
            response_model=UpdateKeypairResourcePolicyResponse,
        )

    async def delete_keypair_policy(
        self, request: DeleteKeypairResourcePolicyRequest
    ) -> DeleteKeypairResourcePolicyResponse:
        return await self._client.typed_request(
            "POST",
            "/admin/resource-policies/keypair/delete",
            request=request,
            response_model=DeleteKeypairResourcePolicyResponse,
        )

    # ---- User Resource Policy ----

    async def create_user_policy(
        self, request: CreateUserResourcePolicyRequest
    ) -> CreateUserResourcePolicyResponse:
        return await self._client.typed_request(
            "POST",
            "/admin/resource-policies/user",
            request=request,
            response_model=CreateUserResourcePolicyResponse,
        )

    async def get_user_policy(self, policy_name: str) -> GetUserResourcePolicyResponse:
        return await self._client.typed_request(
            "GET",
            f"/admin/resource-policies/user/{policy_name}",
            response_model=GetUserResourcePolicyResponse,
        )

    async def search_user_policies(
        self, request: SearchUserResourcePoliciesRequest
    ) -> SearchUserResourcePoliciesResponse:
        return await self._client.typed_request(
            "POST",
            "/admin/resource-policies/user/search",
            request=request,
            response_model=SearchUserResourcePoliciesResponse,
        )

    async def update_user_policy(
        self, policy_name: str, request: UpdateUserResourcePolicyRequest
    ) -> UpdateUserResourcePolicyResponse:
        return await self._client.typed_request(
            "PATCH",
            f"/admin/resource-policies/user/{policy_name}",
            request=request,
            response_model=UpdateUserResourcePolicyResponse,
        )

    async def delete_user_policy(
        self, request: DeleteUserResourcePolicyRequest
    ) -> DeleteUserResourcePolicyResponse:
        return await self._client.typed_request(
            "POST",
            "/admin/resource-policies/user/delete",
            request=request,
            response_model=DeleteUserResourcePolicyResponse,
        )

    # ---- Project Resource Policy ----

    async def create_project_policy(
        self, request: CreateProjectResourcePolicyRequest
    ) -> CreateProjectResourcePolicyResponse:
        return await self._client.typed_request(
            "POST",
            "/admin/resource-policies/project",
            request=request,
            response_model=CreateProjectResourcePolicyResponse,
        )

    async def get_project_policy(self, policy_name: str) -> GetProjectResourcePolicyResponse:
        return await self._client.typed_request(
            "GET",
            f"/admin/resource-policies/project/{policy_name}",
            response_model=GetProjectResourcePolicyResponse,
        )

    async def search_project_policies(
        self, request: SearchProjectResourcePoliciesRequest
    ) -> SearchProjectResourcePoliciesResponse:
        return await self._client.typed_request(
            "POST",
            "/admin/resource-policies/project/search",
            request=request,
            response_model=SearchProjectResourcePoliciesResponse,
        )

    async def update_project_policy(
        self, policy_name: str, request: UpdateProjectResourcePolicyRequest
    ) -> UpdateProjectResourcePolicyResponse:
        return await self._client.typed_request(
            "PATCH",
            f"/admin/resource-policies/project/{policy_name}",
            request=request,
            response_model=UpdateProjectResourcePolicyResponse,
        )

    async def delete_project_policy(
        self, request: DeleteProjectResourcePolicyRequest
    ) -> DeleteProjectResourcePolicyResponse:
        return await self._client.typed_request(
            "POST",
            "/admin/resource-policies/project/delete",
            request=request,
            response_model=DeleteProjectResourcePolicyResponse,
        )
