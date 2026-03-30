"""REST v2 handler for resource policy operations."""

from __future__ import annotations

from http import HTTPStatus

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    AdminSearchKeypairResourcePoliciesInput,
    AdminSearchProjectResourcePoliciesInput,
    AdminSearchUserResourcePoliciesInput,
    CreateKeypairResourcePolicyInput,
    CreateProjectResourcePolicyInput,
    CreateUserResourcePolicyInput,
    DeleteKeypairResourcePolicyInput,
    DeleteProjectResourcePolicyInput,
    DeleteUserResourcePolicyInput,
    UpdateKeypairResourcePolicyInput,
    UpdateProjectResourcePolicyInput,
    UpdateUserResourcePolicyInput,
)
from ai.backend.manager.api.adapters.resource_policy import ResourcePolicyAdapter
from ai.backend.manager.api.rest.v2.path_params import ResourcePolicyNamePathParam


class V2ResourcePolicyHandler:
    """REST v2 handler for keypair, user, and project resource policies."""

    def __init__(self, *, adapter: ResourcePolicyAdapter) -> None:
        self._adapter = adapter

    # ── Keypair Resource Policy ──

    async def admin_get_keypair_resource_policy(
        self,
        path: PathParam[ResourcePolicyNamePathParam],
    ) -> APIResponse:
        result = await self._adapter.admin_get_keypair_resource_policy(path.parsed.name)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search_keypair_resource_policies(
        self,
        body: BodyParam[AdminSearchKeypairResourcePoliciesInput],
    ) -> APIResponse:
        result = await self._adapter.admin_search_keypair_resource_policies(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_create_keypair_resource_policy(
        self,
        body: BodyParam[CreateKeypairResourcePolicyInput],
    ) -> APIResponse:
        result = await self._adapter.admin_create_keypair_resource_policy(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def admin_update_keypair_resource_policy(
        self,
        path: PathParam[ResourcePolicyNamePathParam],
        body: BodyParam[UpdateKeypairResourcePolicyInput],
    ) -> APIResponse:
        result = await self._adapter.admin_update_keypair_resource_policy(
            path.parsed.name, body.parsed
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_delete_keypair_resource_policy(
        self,
        path: PathParam[ResourcePolicyNamePathParam],
    ) -> APIResponse:
        result = await self._adapter.admin_delete_keypair_resource_policy(
            DeleteKeypairResourcePolicyInput(name=path.parsed.name)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def my_keypair_resource_policy(self) -> APIResponse:
        result = await self._adapter.get_my_keypair_resource_policy()
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # ── User Resource Policy ──

    async def admin_get_user_resource_policy(
        self,
        path: PathParam[ResourcePolicyNamePathParam],
    ) -> APIResponse:
        result = await self._adapter.admin_get_user_resource_policy(path.parsed.name)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search_user_resource_policies(
        self,
        body: BodyParam[AdminSearchUserResourcePoliciesInput],
    ) -> APIResponse:
        result = await self._adapter.admin_search_user_resource_policies(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_create_user_resource_policy(
        self,
        body: BodyParam[CreateUserResourcePolicyInput],
    ) -> APIResponse:
        result = await self._adapter.admin_create_user_resource_policy(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def admin_update_user_resource_policy(
        self,
        path: PathParam[ResourcePolicyNamePathParam],
        body: BodyParam[UpdateUserResourcePolicyInput],
    ) -> APIResponse:
        result = await self._adapter.admin_update_user_resource_policy(
            path.parsed.name, body.parsed
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_delete_user_resource_policy(
        self,
        path: PathParam[ResourcePolicyNamePathParam],
    ) -> APIResponse:
        result = await self._adapter.admin_delete_user_resource_policy(
            DeleteUserResourcePolicyInput(name=path.parsed.name)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def my_user_resource_policy(self) -> APIResponse:
        result = await self._adapter.get_my_user_resource_policy()
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # ── Project Resource Policy ──

    async def admin_get_project_resource_policy(
        self,
        path: PathParam[ResourcePolicyNamePathParam],
    ) -> APIResponse:
        result = await self._adapter.admin_get_project_resource_policy(path.parsed.name)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search_project_resource_policies(
        self,
        body: BodyParam[AdminSearchProjectResourcePoliciesInput],
    ) -> APIResponse:
        result = await self._adapter.admin_search_project_resource_policies(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_create_project_resource_policy(
        self,
        body: BodyParam[CreateProjectResourcePolicyInput],
    ) -> APIResponse:
        result = await self._adapter.admin_create_project_resource_policy(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def admin_update_project_resource_policy(
        self,
        path: PathParam[ResourcePolicyNamePathParam],
        body: BodyParam[UpdateProjectResourcePolicyInput],
    ) -> APIResponse:
        result = await self._adapter.admin_update_project_resource_policy(
            path.parsed.name, body.parsed
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_delete_project_resource_policy(
        self,
        path: PathParam[ResourcePolicyNamePathParam],
    ) -> APIResponse:
        result = await self._adapter.admin_delete_project_resource_policy(
            DeleteProjectResourcePolicyInput(name=path.parsed.name)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
