"""HTTP bindings for the existing user-config API."""

from http import HTTPStatus

from ai.backend.common.api_handlers import APIResponse, BodyParam, QueryParam
from ai.backend.common.data.entity.bootstrap_script import BootstrapScript
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.config.request import (
    CreateUserDotfileRequest,
    DeleteUserDotfileRequest,
    GetUserDotfileRequest,
    UpdateBootstrapScriptRequest,
    UpdateUserDotfileRequest,
)
from ai.backend.common.dto.manager.config.response import (
    GetBootstrapScriptResponse,
    ListDotfilesResponse,
    UpdateBootstrapScriptResponse,
)
from ai.backend.common.types import AccessKey
from ai.backend.manager.api.adapters.user.config import UserConfigAdapter
from ai.backend.manager.data.dotfile.types import normalize_newlines
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.dto.user_config_input import (
    CreateDotfileInput,
    DeleteDefaultDotfileInput,
    UpdateDefaultDotfileInput,
)
from ai.backend.manager.services.user.actions.bootstrap_script import (
    GetDefaultBootstrapScriptAction,
    UpdateDefaultBootstrapScriptAction,
)
from ai.backend.manager.services.user.actions.lookup_keypair_owner import (
    LookupKeypairOwnerByAccessKeyAction,
)
from ai.backend.manager.services.user.processors import UserProcessors


class UserConfigHandler:
    _user: UserProcessors
    _user_config: UserConfigAdapter

    def __init__(self, *, user: UserProcessors, user_config: UserConfigAdapter) -> None:
        self._user = user
        self._user_config = user_config

    async def _owner(self, access_key: AccessKey) -> UserID:
        result = await self._user.lookup_keypair_owner.run(
            LookupKeypairOwnerByAccessKeyAction(access_key=access_key)
        )
        return UserID(result.entity_id())

    async def create(
        self, body: BodyParam[CreateUserDotfileRequest], ctx: UserContext
    ) -> APIResponse:
        params = body.parsed
        user_id = UserID(ctx.user_uuid)
        if params.owner_access_key is not None and params.owner_access_key != ctx.access_key:
            user_id = await self._owner(AccessKey(params.owner_access_key))
        result = await self._user_config.create_dotfile(
            CreateDotfileInput(
                user_id=user_id, path=params.path, perm=params.permission, data=params.data
            )
        )
        return APIResponse.build(HTTPStatus.OK, result)

    async def list_or_get(
        self, query: QueryParam[GetUserDotfileRequest], ctx: UserContext
    ) -> APIResponse:
        params = query.parsed
        user_id = UserID(ctx.user_uuid)
        if params.owner_access_key is not None and params.owner_access_key != ctx.access_key:
            user_id = await self._owner(AccessKey(params.owner_access_key))
        if params.path:
            result = await self._user_config.get_default_dotfile(user_id, params.path)
            return APIResponse.build(HTTPStatus.OK, result)
        items = await self._user_config.get_default_dotfiles(user_id)
        return APIResponse.build(HTTPStatus.OK, ListDotfilesResponse(root=items))

    async def update(
        self, body: BodyParam[UpdateUserDotfileRequest], ctx: UserContext
    ) -> APIResponse:
        params = body.parsed
        user_id = UserID(ctx.user_uuid)
        if params.owner_access_key is not None and params.owner_access_key != ctx.access_key:
            user_id = await self._owner(AccessKey(params.owner_access_key))
        result = await self._user_config.update_default_dotfile(
            UpdateDefaultDotfileInput(
                user_id=user_id, path=params.path, perm=params.permission, data=params.data
            )
        )
        return APIResponse.build(HTTPStatus.OK, result)

    async def delete(
        self, query: QueryParam[DeleteUserDotfileRequest], ctx: UserContext
    ) -> APIResponse:
        params = query.parsed
        user_id = UserID(ctx.user_uuid)
        if params.owner_access_key is not None and params.owner_access_key != ctx.access_key:
            user_id = await self._owner(AccessKey(params.owner_access_key))
        result = await self._user_config.delete_default_dotfile(
            DeleteDefaultDotfileInput(user_id=user_id, path=params.path)
        )
        return APIResponse.build(HTTPStatus.OK, result)

    async def update_bootstrap_script(
        self,
        body: BodyParam[UpdateBootstrapScriptRequest],
        ctx: UserContext,
    ) -> APIResponse:
        access_key = AccessKey(ctx.access_key)
        await self._user.update_default_bootstrap_script.run(
            UpdateDefaultBootstrapScriptAction(
                user_id=await self._owner(access_key),
                script=BootstrapScript(normalize_newlines(body.parsed.script).strip()),
            )
        )
        return APIResponse.build(HTTPStatus.OK, UpdateBootstrapScriptResponse())

    async def get_bootstrap_script(
        self,
        ctx: UserContext,
    ) -> APIResponse:
        access_key = AccessKey(ctx.access_key)
        owner_user_id = await self._owner(access_key)
        result = await self._user.get_default_bootstrap_script.run(
            GetDefaultBootstrapScriptAction(user_id=owner_user_id)
        )
        return APIResponse.build(HTTPStatus.OK, GetBootstrapScriptResponse(root=result.script))
