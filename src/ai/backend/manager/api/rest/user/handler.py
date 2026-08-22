"""User admin API handler using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``PathParam``, ``UserContext``) are automatically
extracted by ``_wrap_api_handler`` and responses are returned as
``APIResponse`` objects.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.data.entity.domain import DomainName
from ai.backend.common.data.entity.user import UserID
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
from ai.backend.common.dto.manager.user.response import UserDTO
from ai.backend.common.types import AccessKey
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.data.user.types import UserStatus as ManagerUserStatus
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.dto.user_request import GetUserPathParam, UpdateUserPathParam
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.repositories.user.creators import UserCreatorSpec
from ai.backend.manager.services.domain.actions.lookup import LookupDomainAction
from ai.backend.manager.services.user.actions.create_user import CreateUserAction
from ai.backend.manager.services.user.actions.delete_user import DeleteUserAction
from ai.backend.manager.services.user.actions.get_user import GetUserAction
from ai.backend.manager.services.user.actions.keypair_ops import (
    GetDefaultKeypairsAction,
    SwitchDefaultAccessKeyAction,
)
from ai.backend.manager.services.user.actions.purge_user import PurgeUserAction
from ai.backend.manager.services.user.actions.search_users import GlobalSearchUsersAction
from ai.backend.manager.services.user.actions.update_user import UpdateUserAction
from ai.backend.manager.types import OptionalState

from .adapter import UserAdapter

if TYPE_CHECKING:
    from ai.backend.manager.config.provider import ManagerConfigProvider
    from ai.backend.manager.services.domain.processors import DomainProcessors
    from ai.backend.manager.services.user.processors import UserProcessors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class UserHandler:
    """User admin API handler with constructor-injected dependencies."""

    def __init__(
        self,
        *,
        user: UserProcessors,
        domain: DomainProcessors,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._user = user
        self._domain = domain
        self._config_provider = config_provider
        self._adapter = UserAdapter()

    async def _user_dtos(self, users: Sequence[UserData]) -> list[UserDTO]:
        """Convert users, reading the key each authorizes with for all of them at once."""
        if not users:
            return []
        result = await self._user.get_default_keypairs.run(
            GetDefaultKeypairsAction(user_ids=[UserID(user.id) for user in users])
        )
        keys = {owner: AccessKey(kp.access_key) for owner, kp in result.designated.items()}
        return [self._adapter.convert_to_dto(user, keys.get(UserID(user.id))) for user in users]

    async def _user_dto(self, user: UserData) -> UserDTO:
        return (await self._user_dtos([user]))[0]

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

        domain_id = (
            await self._domain.lookup.run(
                LookupDomainAction(name=DomainName(body.parsed.domain_name))
            )
        ).entity_id()
        action_result = await self._user.create_user.run(
            CreateUserAction(
                domain_id=domain_id,
                creator=creator,
                group_ids=body.parsed.group_ids,
            )
        )

        resp = CreateUserResponse(user=await self._user_dto(action_result.data.user))
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
        action_result = await self._user.get_user.run(
            GetUserAction(user_id=UserID(path.parsed.user_id))
        )

        resp = GetUserResponse(user=await self._user_dto(action_result.user))
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
        searcher = self._adapter.build_searcher(body.parsed)

        action_result = await self._user.global_search.run(
            GlobalSearchUsersAction(searcher=searcher)
        )

        resp = SearchUsersResponse(
            items=await self._user_dtos(action_result.items),
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

        # First get the user to obtain email (required by UpdateUserAction)
        get_result = await self._user.get_user.run(
            GetUserAction(user_id=UserID(path.parsed.user_id))
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

        action_result = await self._user.update_user.run(
            UpdateUserAction(user_id=UserID(path.parsed.user_id), updater=updater)
        )

        if body.parsed.main_access_key is not None:
            await self._user.switch_default_access_key.run(
                SwitchDefaultAccessKeyAction(
                    user_id=UserID(path.parsed.user_id),
                    access_key=AccessKey(body.parsed.main_access_key),
                )
            )

        resp = UpdateUserResponse(user=await self._user_dto(action_result.data))
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

        await self._user.delete_user.run(DeleteUserAction(user_id=UserID(body.parsed.user_id)))

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

        purge_shared = OptionalState[bool].nop()
        delegate_endpoint = OptionalState[bool].nop()
        if body.parsed.purge_shared_vfolders:
            purge_shared = OptionalState.update(body.parsed.purge_shared_vfolders)
        if body.parsed.delegate_endpoint_ownership:
            delegate_endpoint = OptionalState.update(body.parsed.delegate_endpoint_ownership)

        await self._user.purge_user.run(
            PurgeUserAction(
                user_id=UserID(body.parsed.user_id),
                admin_user_id=ctx.user_uuid,
                purge_shared_vfolders=purge_shared,
                delegate_endpoint_ownership=delegate_endpoint,
            )
        )

        resp = PurgeUserResponse(success=True)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)
