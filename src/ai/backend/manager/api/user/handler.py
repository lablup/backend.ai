"""
REST API handlers for admin-level user CRUD management.
Auth-related endpoints (authorize, signup, password) are excluded.
"""

from __future__ import annotations

from collections.abc import Iterable
from http import HTTPStatus

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, api_handler
from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.user import (
    CreateUserRequest,
    CreateUserResponse,
    DeleteUserRequest,
    DeleteUserResponse,
    GetUserResponse,
    PaginationInfo,
    PurgeUserRequest,
    PurgeUserResponse,
    SearchUsersRequest,
    SearchUsersResponse,
    UpdateUserRequest,
    UpdateUserResponse,
)
from ai.backend.common.types import AccessKey
from ai.backend.manager.api.auth import auth_required_for_method
from ai.backend.manager.api.types import CORSOptions, WebMiddleware
from ai.backend.manager.data.user.types import UserInfoContext
from ai.backend.manager.data.user.types import UserStatus as ManagerUserStatus
from ai.backend.manager.dto.context import AuthConfigCtx, ProcessorsCtx
from ai.backend.manager.dto.user_request import GetUserPathParam, UpdateUserPathParam
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.repositories.user.creators import UserCreatorSpec
from ai.backend.manager.services.user.actions.create_user import CreateUserAction
from ai.backend.manager.services.user.actions.delete_user import DeleteUserAction
from ai.backend.manager.services.user.actions.get_user import GetUserAction
from ai.backend.manager.services.user.actions.modify_user import ModifyUserAction
from ai.backend.manager.services.user.actions.purge_user import PurgeUserAction
from ai.backend.manager.services.user.actions.search_users import SearchUsersAction
from ai.backend.manager.types import OptionalState

from .adapter import UserAdapter

__all__ = ("create_app",)


class UserAPIHandler:
    """REST API handler class for admin user operations."""

    def __init__(self) -> None:
        self._adapter = UserAdapter()

    def _check_superadmin(self) -> None:
        me = current_user()
        if me is None or not me.is_superadmin:
            raise NotEnoughPermission("Only superadmin can manage users.")

    @auth_required_for_method
    @api_handler
    async def create_user(
        self,
        body: BodyParam[CreateUserRequest],
        processors_ctx: ProcessorsCtx,
        auth_config_ctx: AuthConfigCtx,
    ) -> APIResponse:
        """Create a new user."""
        self._check_superadmin()
        processors = processors_ctx.processors
        auth_config = auth_config_ctx.auth_config

        password_info = PasswordInfo(
            password=body.parsed.password,
            algorithm=auth_config.password_hash_algorithm,
            rounds=auth_config.password_hash_rounds,
            salt_size=auth_config.password_hash_salt_size,
        )

        creator = Creator(
            spec=UserCreatorSpec(
                email=body.parsed.email,
                username=body.parsed.username,
                password=password_info,
                need_password_change=body.parsed.need_password_change,
                domain_name=body.parsed.domain_name,
                full_name=body.parsed.full_name,
                description=body.parsed.description,
                status=ManagerUserStatus(body.parsed.status.value)
                if body.parsed.status is not None
                else None,
                role=body.parsed.role.value if body.parsed.role is not None else None,
                allowed_client_ip=body.parsed.allowed_client_ip,
                totp_activated=body.parsed.totp_activated,
                resource_policy=body.parsed.resource_policy,
                sudo_session_enabled=body.parsed.sudo_session_enabled,
                container_uid=body.parsed.container_uid,
                container_main_gid=body.parsed.container_main_gid,
                container_gids=body.parsed.container_gids,
            )
        )

        action_result = await processors.user.create_user.wait_for_complete(
            CreateUserAction(creator=creator, group_ids=body.parsed.group_ids)
        )

        resp = CreateUserResponse(user=self._adapter.convert_to_dto(action_result.data.user))
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get_user(
        self,
        path: PathParam[GetUserPathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get a specific user by ID."""
        self._check_superadmin()
        processors = processors_ctx.processors

        action_result = await processors.user.get_user.wait_for_complete(
            GetUserAction(user_uuid=path.parsed.user_id)
        )

        resp = GetUserResponse(user=self._adapter.convert_to_dto(action_result.user))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def search_users(
        self,
        body: BodyParam[SearchUsersRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Search users with filters, orders, and pagination."""
        self._check_superadmin()
        processors = processors_ctx.processors

        querier = self._adapter.build_querier(body.parsed)

        action_result = await processors.user.search_users.wait_for_complete(
            SearchUsersAction(querier=querier)
        )

        resp = SearchUsersResponse(
            items=[self._adapter.convert_to_dto(u) for u in action_result.users],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def update_user(
        self,
        path: PathParam[UpdateUserPathParam],
        body: BodyParam[UpdateUserRequest],
        processors_ctx: ProcessorsCtx,
        auth_config_ctx: AuthConfigCtx,
    ) -> APIResponse:
        """Update an existing user."""
        self._check_superadmin()
        processors = processors_ctx.processors
        auth_config = auth_config_ctx.auth_config

        # First get the user to obtain email (required by ModifyUserAction)
        get_result = await processors.user.get_user.wait_for_complete(
            GetUserAction(user_uuid=path.parsed.user_id)
        )
        email = get_result.user.email

        # Build password info if password is being updated
        password_info: PasswordInfo | None = None
        if body.parsed.password is not None:
            password_info = PasswordInfo(
                password=body.parsed.password,
                algorithm=auth_config.password_hash_algorithm,
                rounds=auth_config.password_hash_rounds,
                salt_size=auth_config.password_hash_salt_size,
            )

        updater = self._adapter.build_updater(body.parsed, email, password_info)

        action_result = await processors.user.modify_user.wait_for_complete(
            ModifyUserAction(email=email, updater=updater)
        )

        resp = UpdateUserResponse(user=self._adapter.convert_to_dto(action_result.data))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def delete_user(
        self,
        body: BodyParam[DeleteUserRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Soft-delete a user."""
        self._check_superadmin()
        processors = processors_ctx.processors

        # Get user email from UUID
        get_result = await processors.user.get_user.wait_for_complete(
            GetUserAction(user_uuid=body.parsed.user_id)
        )

        await processors.user.delete_user.wait_for_complete(
            DeleteUserAction(email=get_result.user.email)
        )

        resp = DeleteUserResponse(success=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def purge_user(
        self,
        body: BodyParam[PurgeUserRequest],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Permanently purge a user and all associated resources."""
        self._check_superadmin()
        me = current_user()
        if me is None:
            raise NotEnoughPermission("Authentication required.")
        processors = processors_ctx.processors

        # Get user data for purge context
        get_result = await processors.user.get_user.wait_for_complete(
            GetUserAction(user_uuid=body.parsed.user_id)
        )

        # Get caller's info for delegation context
        caller_result = await processors.user.get_user.wait_for_complete(
            GetUserAction(user_uuid=me.user_id)
        )

        user_info_ctx = UserInfoContext(
            uuid=caller_result.user.uuid,
            email=caller_result.user.email,
            main_access_key=AccessKey(caller_result.user.main_access_key or ""),
        )

        purge_shared = OptionalState[bool].nop()
        delegate_endpoint = OptionalState[bool].nop()
        if body.parsed.purge_shared_vfolders:
            purge_shared = OptionalState.update(body.parsed.purge_shared_vfolders)
        if body.parsed.delegate_endpoint_ownership:
            delegate_endpoint = OptionalState.update(body.parsed.delegate_endpoint_ownership)

        await processors.user.purge_user.wait_for_complete(
            PurgeUserAction(
                user_info_ctx=user_info_ctx,
                email=get_result.user.email,
                purge_shared_vfolders=purge_shared,
                delegate_endpoint_ownership=delegate_endpoint,
            )
        )

        resp = PurgeUserResponse(success=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    """Create aiohttp application for user admin API endpoints."""
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "admin/users"

    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    handler = UserAPIHandler()

    cors.add(app.router.add_route("POST", "", handler.create_user))
    cors.add(app.router.add_route("GET", "/{user_id}", handler.get_user))
    cors.add(app.router.add_route("POST", "/search", handler.search_users))
    cors.add(app.router.add_route("PATCH", "/{user_id}", handler.update_user))
    cors.add(app.router.add_route("POST", "/delete", handler.delete_user))
    cors.add(app.router.add_route("POST", "/purge", handler.purge_user))

    return app, []
