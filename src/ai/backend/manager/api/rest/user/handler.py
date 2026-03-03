"""User admin API handler using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``PathParam``, ``UserContext``) are automatically
extracted by ``_wrap_api_handler`` and responses are returned as
``APIResponse`` objects.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
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
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.user.types import UserInfoContext
from ai.backend.manager.data.user.types import UserStatus as ManagerUserStatus
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.dto.user_request import GetUserPathParam, UpdateUserPathParam
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

if TYPE_CHECKING:
    from ai.backend.manager.config.provider import ManagerConfigProvider
    from ai.backend.manager.services.processors import Processors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class UserHandler:
    """User admin API handler with constructor-injected dependencies."""

    def __init__(self, *, processors: Processors, config_provider: ManagerConfigProvider) -> None:
        self._processors = processors
        self._config_provider = config_provider
        self._adapter = UserAdapter()

    # ------------------------------------------------------------------
    # create_user (POST /admin/users)
    # ------------------------------------------------------------------

    async def create_user(
        self,
        body: BodyParam[CreateUserRequest],
        ctx: UserContext,
    ) -> APIResponse:
        log.info("CREATE_USER (ak:{})", ctx.access_key)
        password_info = PasswordInfo(
            password=body.parsed.password,
            algorithm=self._config_provider.config.auth.password_hash_algorithm,
            rounds=self._config_provider.config.auth.password_hash_rounds,
            salt_size=self._config_provider.config.auth.password_hash_salt_size,
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

        action_result = await self._processors.user.create_user.wait_for_complete(
            CreateUserAction(creator=creator, group_ids=body.parsed.group_ids)
        )

        resp = CreateUserResponse(user=self._adapter.convert_to_dto(action_result.data.user))
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    # ------------------------------------------------------------------
    # get_user (GET /admin/users/{user_id})
    # ------------------------------------------------------------------

    async def get_user(
        self,
        path: PathParam[GetUserPathParam],
        ctx: UserContext,
    ) -> APIResponse:
        log.info("GET_USER (ak:{}, u:{})", ctx.access_key, path.parsed.user_id)
        action_result = await self._processors.user.get_user.wait_for_complete(
            GetUserAction(user_uuid=path.parsed.user_id)
        )

        resp = GetUserResponse(user=self._adapter.convert_to_dto(action_result.user))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # ------------------------------------------------------------------
    # search_users (POST /admin/users/search)
    # ------------------------------------------------------------------

    async def search_users(
        self,
        body: BodyParam[SearchUsersRequest],
        ctx: UserContext,
    ) -> APIResponse:
        log.info("SEARCH_USERS (ak:{})", ctx.access_key)
        querier = self._adapter.build_querier(body.parsed)

        action_result = await self._processors.user.search_users.wait_for_complete(
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

    # ------------------------------------------------------------------
    # update_user (PATCH /admin/users/{user_id})
    # ------------------------------------------------------------------

    async def update_user(
        self,
        path: PathParam[UpdateUserPathParam],
        body: BodyParam[UpdateUserRequest],
        ctx: UserContext,
    ) -> APIResponse:
        log.info("UPDATE_USER (ak:{}, u:{})", ctx.access_key, path.parsed.user_id)

        # First get the user to obtain email (required by ModifyUserAction)
        get_result = await self._processors.user.get_user.wait_for_complete(
            GetUserAction(user_uuid=path.parsed.user_id)
        )
        email = get_result.user.email

        # Build password info if password is being updated
        password_info: PasswordInfo | None = None
        if body.parsed.password is not None:
            password_info = PasswordInfo(
                password=body.parsed.password,
                algorithm=self._config_provider.config.auth.password_hash_algorithm,
                rounds=self._config_provider.config.auth.password_hash_rounds,
                salt_size=self._config_provider.config.auth.password_hash_salt_size,
            )

        updater = self._adapter.build_updater(body.parsed, email, password_info)

        action_result = await self._processors.user.modify_user.wait_for_complete(
            ModifyUserAction(email=email, updater=updater)
        )

        resp = UpdateUserResponse(user=self._adapter.convert_to_dto(action_result.data))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # ------------------------------------------------------------------
    # delete_user (POST /admin/users/delete)
    # ------------------------------------------------------------------

    async def delete_user(
        self,
        body: BodyParam[DeleteUserRequest],
        ctx: UserContext,
    ) -> APIResponse:
        log.info("DELETE_USER (ak:{}, u:{})", ctx.access_key, body.parsed.user_id)

        # Get user email from UUID
        get_result = await self._processors.user.get_user.wait_for_complete(
            GetUserAction(user_uuid=body.parsed.user_id)
        )

        await self._processors.user.delete_user.wait_for_complete(
            DeleteUserAction(email=get_result.user.email)
        )

        resp = DeleteUserResponse(success=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # ------------------------------------------------------------------
    # purge_user (POST /admin/users/purge)
    # ------------------------------------------------------------------

    async def purge_user(
        self,
        body: BodyParam[PurgeUserRequest],
        ctx: UserContext,
    ) -> APIResponse:
        log.info("PURGE_USER (ak:{}, u:{})", ctx.access_key, body.parsed.user_id)

        # Get user data for purge context
        get_result = await self._processors.user.get_user.wait_for_complete(
            GetUserAction(user_uuid=body.parsed.user_id)
        )

        # Get caller's info for delegation context
        caller_result = await self._processors.user.get_user.wait_for_complete(
            GetUserAction(user_uuid=ctx.user_uuid)
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

        await self._processors.user.purge_user.wait_for_complete(
            PurgeUserAction(
                user_info_ctx=user_info_ctx,
                email=get_result.user.email,
                purge_shared_vfolders=purge_shared,
                delegate_endpoint_ownership=delegate_endpoint,
            )
        )

        resp = PurgeUserResponse(success=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)
