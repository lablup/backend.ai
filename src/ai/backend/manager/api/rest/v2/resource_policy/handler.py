"""REST v2 handler for resource policy operations."""

from __future__ import annotations

from http import HTTPStatus

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyUUID,
    ProjectResourcePolicyUUID,
    UserResourcePolicyUUID,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    AdminSearchKeypairResourcePoliciesInput,
    AdminSearchProjectResourcePoliciesInput,
    AdminSearchUserResourcePoliciesInput,
    CreateKeypairResourcePolicyInput,
    CreateProjectResourcePolicyInput,
    CreateUserResourcePolicyInput,
    PartialBulkPurgeKeypairResourcePoliciesInput,
    PartialBulkPurgeProjectResourcePoliciesInput,
    PartialBulkPurgeUserResourcePoliciesInput,
    PartialBulkUpdateKeypairResourcePoliciesInput,
    PartialBulkUpdateProjectResourcePoliciesInput,
    PartialBulkUpdateUserResourcePoliciesInput,
    UpdateKeypairResourcePolicyInput,
    UpdateProjectResourcePolicyInput,
    UpdateUserResourcePolicyInput,
)
from ai.backend.manager.api.adapters.resource_policy.adapter import ResourcePolicyAdapter
from ai.backend.manager.api.rest.v2.path_params import (
    ProjectIdPathParam,
    ResourcePolicyIdPathParam,
    ResourcePolicyNamePathParam,
)


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

    async def update_keypair_resource_policy(
        self,
        path: PathParam[ResourcePolicyIdPathParam],
        body: BodyParam[UpdateKeypairResourcePolicyInput],
    ) -> APIResponse:
        """Update a keypair resource policy."""
        result = await self._adapter.update_keypair_resource_policy(
            KeyPairResourcePolicyUUID(path.parsed.policy_id), body.parsed
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def purge_keypair_resource_policy(
        self,
        path: PathParam[ResourcePolicyIdPathParam],
    ) -> APIResponse:
        """Permanently remove a keypair resource policy."""
        result = await self._adapter.purge_keypair_resource_policy(
            KeyPairResourcePolicyUUID(path.parsed.policy_id)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_update_keypair_resource_policies(
        self,
        body: BodyParam[PartialBulkUpdateKeypairResourcePoliciesInput],
    ) -> APIResponse:
        """Update several keypair resource policies, answering for each one."""
        result = await self._adapter.partial_bulk_update_keypair_resource_policies(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_purge_keypair_resource_policies(
        self,
        body: BodyParam[PartialBulkPurgeKeypairResourcePoliciesInput],
    ) -> APIResponse:
        """Permanently remove several keypair resource policies, answering for each one."""
        result = await self._adapter.partial_bulk_purge_keypair_resource_policies(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_update_keypair_resource_policy(
        self,
        path: PathParam[ResourcePolicyNamePathParam],
        body: BodyParam[UpdateKeypairResourcePolicyInput],
    ) -> APIResponse:
        """Deprecated. Use `PATCH /v2/resource-policies/keypair/{policy_id}`."""
        policy_id = await self._adapter.lookup_keypair_resource_policy(path.parsed.name)
        result = await self._adapter.update_keypair_resource_policy(policy_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_delete_keypair_resource_policy(
        self,
        path: PathParam[ResourcePolicyNamePathParam],
    ) -> APIResponse:
        """Deprecated. Use `DELETE /v2/resource-policies/keypair/{policy_id}`."""
        policy_id = await self._adapter.lookup_keypair_resource_policy(path.parsed.name)
        result = await self._adapter.purge_keypair_resource_policy(policy_id)
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

    async def update_user_resource_policy(
        self,
        path: PathParam[ResourcePolicyIdPathParam],
        body: BodyParam[UpdateUserResourcePolicyInput],
    ) -> APIResponse:
        """Update a user resource policy."""
        result = await self._adapter.update_user_resource_policy(
            UserResourcePolicyUUID(path.parsed.policy_id), body.parsed
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def purge_user_resource_policy(
        self,
        path: PathParam[ResourcePolicyIdPathParam],
    ) -> APIResponse:
        """Permanently remove a user resource policy."""
        result = await self._adapter.purge_user_resource_policy(
            UserResourcePolicyUUID(path.parsed.policy_id)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_update_user_resource_policies(
        self,
        body: BodyParam[PartialBulkUpdateUserResourcePoliciesInput],
    ) -> APIResponse:
        """Update several user resource policies, answering for each one."""
        result = await self._adapter.partial_bulk_update_user_resource_policies(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_purge_user_resource_policies(
        self,
        body: BodyParam[PartialBulkPurgeUserResourcePoliciesInput],
    ) -> APIResponse:
        """Permanently remove several user resource policies, answering for each one."""
        result = await self._adapter.partial_bulk_purge_user_resource_policies(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_update_user_resource_policy(
        self,
        path: PathParam[ResourcePolicyNamePathParam],
        body: BodyParam[UpdateUserResourcePolicyInput],
    ) -> APIResponse:
        """Deprecated. Use `PATCH /v2/resource-policies/user/{policy_id}`."""
        policy_id = await self._adapter.lookup_user_resource_policy(path.parsed.name)
        result = await self._adapter.update_user_resource_policy(policy_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_delete_user_resource_policy(
        self,
        path: PathParam[ResourcePolicyNamePathParam],
    ) -> APIResponse:
        """Deprecated. Use `DELETE /v2/resource-policies/user/{policy_id}`."""
        policy_id = await self._adapter.lookup_user_resource_policy(path.parsed.name)
        result = await self._adapter.purge_user_resource_policy(policy_id)
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

    async def update_project_resource_policy(
        self,
        path: PathParam[ResourcePolicyIdPathParam],
        body: BodyParam[UpdateProjectResourcePolicyInput],
    ) -> APIResponse:
        """Update a project resource policy."""
        result = await self._adapter.update_project_resource_policy(
            ProjectResourcePolicyUUID(path.parsed.policy_id), body.parsed
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def purge_project_resource_policy(
        self,
        path: PathParam[ResourcePolicyIdPathParam],
    ) -> APIResponse:
        """Permanently remove a project resource policy."""
        result = await self._adapter.purge_project_resource_policy(
            ProjectResourcePolicyUUID(path.parsed.policy_id)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_update_project_resource_policies(
        self,
        body: BodyParam[PartialBulkUpdateProjectResourcePoliciesInput],
    ) -> APIResponse:
        """Update several project resource policies, answering for each one."""
        result = await self._adapter.partial_bulk_update_project_resource_policies(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_purge_project_resource_policies(
        self,
        body: BodyParam[PartialBulkPurgeProjectResourcePoliciesInput],
    ) -> APIResponse:
        """Permanently remove several project resource policies, answering for each one."""
        result = await self._adapter.partial_bulk_purge_project_resource_policies(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_update_project_resource_policy(
        self,
        path: PathParam[ResourcePolicyNamePathParam],
        body: BodyParam[UpdateProjectResourcePolicyInput],
    ) -> APIResponse:
        """Deprecated. Use `PATCH /v2/resource-policies/project/{policy_id}`."""
        policy_id = await self._adapter.lookup_project_resource_policy(path.parsed.name)
        result = await self._adapter.update_project_resource_policy(policy_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_delete_project_resource_policy(
        self,
        path: PathParam[ResourcePolicyNamePathParam],
    ) -> APIResponse:
        """Deprecated. Use `DELETE /v2/resource-policies/project/{policy_id}`."""
        policy_id = await self._adapter.lookup_project_resource_policy(path.parsed.name)
        result = await self._adapter.purge_project_resource_policy(policy_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def scoped_project_resource_policy(
        self,
        path: PathParam[ProjectIdPathParam],
    ) -> APIResponse:
        result = await self._adapter.get_project_resource_policy(ProjectID(path.parsed.project_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
