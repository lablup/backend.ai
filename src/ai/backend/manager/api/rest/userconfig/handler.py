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
from ai.backend.manager.services.auth.actions.resolve_access_key_scope import (
    PublicResolveAccessKeyScopeAction,
)
from ai.backend.manager.services.auth.processors import AuthProcessors
from ai.backend.manager.services.user.actions.bootstrap_script import (
    GetDefaultBootstrapScriptAction,
    UpdateDefaultBootstrapScriptAction,
)
from ai.backend.manager.services.user.actions.lookup_keypair_owner import (
    LookupKeypairOwnerByAccessKeyAction,
)
from ai.backend.manager.services.user.processors import UserProcessors


class UserConfigHandler:
    _auth: AuthProcessors
    _user: UserProcessors
    _user_config: UserConfigAdapter

    def __init__(
        self, *, auth: AuthProcessors, user: UserProcessors, user_config: UserConfigAdapter
    ) -> None:
        self._auth = auth
        self._user = user
        self._user_config = user_config

    async def _lookup_keypair_owner(self, access_key: AccessKey) -> UserID:
        result = await self._user.lookup_keypair_owner.run(
            LookupKeypairOwnerByAccessKeyAction(access_key=access_key)
        )
        return UserID(result.entity_id())

    async def _authorize_keypair_owner(self, requester_id: UserID, owner_access_key: str) -> UserID:
        """Another user's key needs delegation rights; the requester's own keys do not."""
        owner_id = await self._lookup_keypair_owner(AccessKey(owner_access_key))
        if owner_id != requester_id:
            await self._auth.public_resolve_access_key_scope.run(
                PublicResolveAccessKeyScopeAction(owner_access_key=owner_access_key)
            )
        return owner_id

    async def create(
        self, body: BodyParam[CreateUserDotfileRequest], ctx: UserContext
    ) -> APIResponse:
        params = body.parsed
        user_id = UserID(ctx.user_uuid)
        if params.owner_access_key is not None:
            user_id = await self._authorize_keypair_owner(user_id, params.owner_access_key)
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
        if params.owner_access_key is not None:
            user_id = await self._authorize_keypair_owner(user_id, params.owner_access_key)
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
        if params.owner_access_key is not None:
            user_id = await self._authorize_keypair_owner(user_id, params.owner_access_key)
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
        if params.owner_access_key is not None:
            user_id = await self._authorize_keypair_owner(user_id, params.owner_access_key)
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
        owner_user_id = await self._lookup_keypair_owner(access_key)
        await self._user.update_default_bootstrap_script.run(
            UpdateDefaultBootstrapScriptAction(
                user_id=owner_user_id,
                script=BootstrapScript(normalize_newlines(body.parsed.script).strip()),
                creator_id=owner_user_id,
            )
        )
        return APIResponse.build(HTTPStatus.OK, UpdateBootstrapScriptResponse())

    async def get_bootstrap_script(
        self,
        ctx: UserContext,
    ) -> APIResponse:
        access_key = AccessKey(ctx.access_key)
        owner_user_id = await self._lookup_keypair_owner(access_key)
        result = await self._user.get_default_bootstrap_script.run(
            GetDefaultBootstrapScriptAction(user_id=owner_user_id)
        )
        return APIResponse.build(HTTPStatus.OK, GetBootstrapScriptResponse(root=result.script))
