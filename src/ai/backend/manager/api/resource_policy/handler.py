"""
REST API handlers for resource policy management.
Provides CRUD endpoints for keypair, user, and project resource policy operations.
"""

from __future__ import annotations

from collections.abc import Iterable
from http import HTTPStatus

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, api_handler
from ai.backend.common.contexts.user import current_user
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
    PaginationInfo,
    SearchKeypairResourcePoliciesResponse,
    SearchProjectResourcePoliciesResponse,
    SearchUserResourcePoliciesResponse,
    UpdateKeypairResourcePolicyResponse,
    UpdateProjectResourcePolicyResponse,
    UpdateUserResourcePolicyResponse,
)
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api.auth import auth_required_for_method
from ai.backend.manager.api.types import CORSOptions, WebMiddleware
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.dto.resource_policy_request import (
    GetResourcePolicyPathParam,
    UpdateResourcePolicyPathParam,
)
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.keypair_resource_policy.creators import (
    KeyPairResourcePolicyCreatorSpec,
)
from ai.backend.manager.repositories.project_resource_policy.creators import (
    ProjectResourcePolicyCreatorSpec,
)
from ai.backend.manager.repositories.user_resource_policy.creators import (
    UserResourcePolicyCreatorSpec,
)
from ai.backend.manager.services.keypair_resource_policy.actions.create_keypair_resource_policy import (
    CreateKeyPairResourcePolicyAction,
)
from ai.backend.manager.services.keypair_resource_policy.actions.delete_keypair_resource_policy import (
    DeleteKeyPairResourcePolicyAction,
)
from ai.backend.manager.services.keypair_resource_policy.actions.get_keypair_resource_policy import (
    GetKeyPairResourcePolicyAction,
)
from ai.backend.manager.services.keypair_resource_policy.actions.modify_keypair_resource_policy import (
    ModifyKeyPairResourcePolicyAction,
)
from ai.backend.manager.services.keypair_resource_policy.actions.search_keypair_resource_policies import (
    SearchKeyPairResourcePoliciesAction,
)
from ai.backend.manager.services.project_resource_policy.actions.create_project_resource_policy import (
    CreateProjectResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.actions.delete_project_resource_policy import (
    DeleteProjectResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.actions.get_project_resource_policy import (
    GetProjectResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.actions.modify_project_resource_policy import (
    ModifyProjectResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.actions.search_project_resource_policies import (
    SearchProjectResourcePoliciesAction,
)
from ai.backend.manager.services.user_resource_policy.actions.create_user_resource_policy import (
    CreateUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.delete_user_resource_policy import (
    DeleteUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.get_user_resource_policy import (
    GetUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.modify_user_resource_policy import (
    ModifyUserResourcePolicyAction,
)
from ai.backend.manager.services.user_resource_policy.actions.search_user_resource_policies import (
    SearchUserResourcePoliciesAction,
)

from .adapter import ResourcePolicyAdapter

__all__ = ("create_app",)


class KeypairResourcePolicyHandler:
    """REST API handler for keypair resource policy operations."""

    def __init__(self, adapter: ResourcePolicyAdapter) -> None:
        self.adapter = adapter

    @auth_required_for_method
    @api_handler
    async def create(
        self,
        body: BodyParam[CreateKeypairResourcePolicyRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise GenericForbidden()

        creator = Creator(
            spec=KeyPairResourcePolicyCreatorSpec(
                name=body.parsed.name,
                default_for_unspecified=body.parsed.default_for_unspecified,
                total_resource_slots=ResourceSlot(body.parsed.total_resource_slots),
                max_session_lifetime=body.parsed.max_session_lifetime,
                max_concurrent_sessions=body.parsed.max_concurrent_sessions,
                max_pending_session_count=body.parsed.max_pending_session_count,
                max_pending_session_resource_slots=(
                    ResourceSlot(body.parsed.max_pending_session_resource_slots)
                    if body.parsed.max_pending_session_resource_slots is not None
                    else None
                ),
                max_concurrent_sftp_sessions=body.parsed.max_concurrent_sftp_sessions,
                max_containers_per_session=body.parsed.max_containers_per_session,
                idle_timeout=body.parsed.idle_timeout,
                allowed_vfolder_hosts=body.parsed.allowed_vfolder_hosts,
                max_quota_scope_size=None,
                max_vfolder_count=None,
                max_vfolder_size=None,
            )
        )

        action_result = await processors.keypair_resource_policy.create_keypair_resource_policy.wait_for_complete(
            CreateKeyPairResourcePolicyAction(creator=creator)
        )

        resp = CreateKeypairResourcePolicyResponse(
            item=self.adapter.convert_keypair_to_dto(action_result.keypair_resource_policy)
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get(
        self,
        path: PathParam[GetResourcePolicyPathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise GenericForbidden()

        action_result = (
            await processors.keypair_resource_policy.get_keypair_resource_policy.wait_for_complete(
                GetKeyPairResourcePolicyAction(name=path.parsed.policy_name)
            )
        )

        resp = GetKeypairResourcePolicyResponse(
            item=self.adapter.convert_keypair_to_dto(action_result.keypair_resource_policy)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search(
        self,
        body: BodyParam[SearchKeypairResourcePoliciesRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise GenericForbidden()

        querier = self.adapter.build_keypair_querier(body.parsed)

        action_result = await processors.keypair_resource_policy.search_keypair_resource_policies.wait_for_complete(
            SearchKeyPairResourcePoliciesAction(querier=querier)
        )

        resp = SearchKeypairResourcePoliciesResponse(
            items=[self.adapter.convert_keypair_to_dto(d) for d in action_result.items],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def update(
        self,
        path: PathParam[UpdateResourcePolicyPathParam],
        body: BodyParam[UpdateKeypairResourcePolicyRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise GenericForbidden()

        policy_name = path.parsed.policy_name
        updater = self.adapter.build_keypair_updater(body.parsed, policy_name)

        action_result = await processors.keypair_resource_policy.modify_keypair_resource_policy.wait_for_complete(
            ModifyKeyPairResourcePolicyAction(name=policy_name, updater=updater)
        )

        resp = UpdateKeypairResourcePolicyResponse(
            item=self.adapter.convert_keypair_to_dto(action_result.keypair_resource_policy)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def delete(
        self,
        body: BodyParam[DeleteKeypairResourcePolicyRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise GenericForbidden()

        await processors.keypair_resource_policy.delete_keypair_resource_policy.wait_for_complete(
            DeleteKeyPairResourcePolicyAction(name=body.parsed.name)
        )

        resp = DeleteKeypairResourcePolicyResponse(deleted=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


class UserResourcePolicyHandler:
    """REST API handler for user resource policy operations."""

    def __init__(self, adapter: ResourcePolicyAdapter) -> None:
        self.adapter = adapter

    @auth_required_for_method
    @api_handler
    async def create(
        self,
        body: BodyParam[CreateUserResourcePolicyRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise GenericForbidden()

        creator = Creator(
            spec=UserResourcePolicyCreatorSpec(
                name=body.parsed.name,
                max_vfolder_count=body.parsed.max_vfolder_count,
                max_quota_scope_size=body.parsed.max_quota_scope_size,
                max_session_count_per_model_session=body.parsed.max_session_count_per_model_session,
                max_customized_image_count=body.parsed.max_customized_image_count,
            )
        )

        action_result = (
            await processors.user_resource_policy.create_user_resource_policy.wait_for_complete(
                CreateUserResourcePolicyAction(creator=creator)
            )
        )

        resp = CreateUserResourcePolicyResponse(
            item=self.adapter.convert_user_to_dto(action_result.user_resource_policy)
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get(
        self,
        path: PathParam[GetResourcePolicyPathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise GenericForbidden()

        action_result = (
            await processors.user_resource_policy.get_user_resource_policy.wait_for_complete(
                GetUserResourcePolicyAction(name=path.parsed.policy_name)
            )
        )

        resp = GetUserResourcePolicyResponse(
            item=self.adapter.convert_user_to_dto(action_result.user_resource_policy)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search(
        self,
        body: BodyParam[SearchUserResourcePoliciesRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise GenericForbidden()

        querier = self.adapter.build_user_querier(body.parsed)

        action_result = (
            await processors.user_resource_policy.search_user_resource_policies.wait_for_complete(
                SearchUserResourcePoliciesAction(querier=querier)
            )
        )

        resp = SearchUserResourcePoliciesResponse(
            items=[self.adapter.convert_user_to_dto(d) for d in action_result.items],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def update(
        self,
        path: PathParam[UpdateResourcePolicyPathParam],
        body: BodyParam[UpdateUserResourcePolicyRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise GenericForbidden()

        policy_name = path.parsed.policy_name
        updater = self.adapter.build_user_updater(body.parsed, policy_name)

        action_result = (
            await processors.user_resource_policy.modify_user_resource_policy.wait_for_complete(
                ModifyUserResourcePolicyAction(name=policy_name, updater=updater)
            )
        )

        resp = UpdateUserResourcePolicyResponse(
            item=self.adapter.convert_user_to_dto(action_result.user_resource_policy)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def delete(
        self,
        body: BodyParam[DeleteUserResourcePolicyRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise GenericForbidden()

        await processors.user_resource_policy.delete_user_resource_policy.wait_for_complete(
            DeleteUserResourcePolicyAction(name=body.parsed.name)
        )

        resp = DeleteUserResourcePolicyResponse(deleted=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


class ProjectResourcePolicyHandler:
    """REST API handler for project resource policy operations."""

    def __init__(self, adapter: ResourcePolicyAdapter) -> None:
        self.adapter = adapter

    @auth_required_for_method
    @api_handler
    async def create(
        self,
        body: BodyParam[CreateProjectResourcePolicyRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise GenericForbidden()

        creator = Creator(
            spec=ProjectResourcePolicyCreatorSpec(
                name=body.parsed.name,
                max_vfolder_count=body.parsed.max_vfolder_count,
                max_quota_scope_size=body.parsed.max_quota_scope_size,
                max_network_count=body.parsed.max_network_count,
            )
        )

        action_result = await processors.project_resource_policy.create_project_resource_policy.wait_for_complete(
            CreateProjectResourcePolicyAction(creator=creator)
        )

        resp = CreateProjectResourcePolicyResponse(
            item=self.adapter.convert_project_to_dto(action_result.project_resource_policy)
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get(
        self,
        path: PathParam[GetResourcePolicyPathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise GenericForbidden()

        action_result = (
            await processors.project_resource_policy.get_project_resource_policy.wait_for_complete(
                GetProjectResourcePolicyAction(name=path.parsed.policy_name)
            )
        )

        resp = GetProjectResourcePolicyResponse(
            item=self.adapter.convert_project_to_dto(action_result.project_resource_policy)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search(
        self,
        body: BodyParam[SearchProjectResourcePoliciesRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise GenericForbidden()

        querier = self.adapter.build_project_querier(body.parsed)

        action_result = await processors.project_resource_policy.search_project_resource_policies.wait_for_complete(
            SearchProjectResourcePoliciesAction(querier=querier)
        )

        resp = SearchProjectResourcePoliciesResponse(
            items=[self.adapter.convert_project_to_dto(d) for d in action_result.items],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def update(
        self,
        path: PathParam[UpdateResourcePolicyPathParam],
        body: BodyParam[UpdateProjectResourcePolicyRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise GenericForbidden()

        policy_name = path.parsed.policy_name
        updater = self.adapter.build_project_updater(body.parsed, policy_name)

        action_result = await processors.project_resource_policy.modify_project_resource_policy.wait_for_complete(
            ModifyProjectResourcePolicyAction(name=policy_name, updater=updater)
        )

        resp = UpdateProjectResourcePolicyResponse(
            item=self.adapter.convert_project_to_dto(action_result.project_resource_policy)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def delete(
        self,
        body: BodyParam[DeleteProjectResourcePolicyRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        processors = processors_ctx.processors
        me = current_user()
        if me is None or not me.is_superadmin:
            raise GenericForbidden()

        await processors.project_resource_policy.delete_project_resource_policy.wait_for_complete(
            DeleteProjectResourcePolicyAction(name=body.parsed.name)
        )

        resp = DeleteProjectResourcePolicyResponse(deleted=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    """Create aiohttp application for resource policy API endpoints."""
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "admin/resource-policies"

    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    adapter = ResourcePolicyAdapter()
    keypair_handler = KeypairResourcePolicyHandler(adapter)
    user_handler = UserResourcePolicyHandler(adapter)
    project_handler = ProjectResourcePolicyHandler(adapter)

    # Keypair resource policy routes
    cors.add(app.router.add_route("POST", "/keypair", keypair_handler.create))
    cors.add(app.router.add_route("GET", "/keypair/{policy_name}", keypair_handler.get))
    cors.add(app.router.add_route("POST", "/keypair/search", keypair_handler.search))
    cors.add(app.router.add_route("PATCH", "/keypair/{policy_name}", keypair_handler.update))
    cors.add(app.router.add_route("POST", "/keypair/delete", keypair_handler.delete))

    # User resource policy routes
    cors.add(app.router.add_route("POST", "/user", user_handler.create))
    cors.add(app.router.add_route("GET", "/user/{policy_name}", user_handler.get))
    cors.add(app.router.add_route("POST", "/user/search", user_handler.search))
    cors.add(app.router.add_route("PATCH", "/user/{policy_name}", user_handler.update))
    cors.add(app.router.add_route("POST", "/user/delete", user_handler.delete))

    # Project resource policy routes
    cors.add(app.router.add_route("POST", "/project", project_handler.create))
    cors.add(app.router.add_route("GET", "/project/{policy_name}", project_handler.get))
    cors.add(app.router.add_route("POST", "/project/search", project_handler.search))
    cors.add(app.router.add_route("PATCH", "/project/{policy_name}", project_handler.update))
    cors.add(app.router.add_route("POST", "/project/delete", project_handler.delete))

    return app, []
