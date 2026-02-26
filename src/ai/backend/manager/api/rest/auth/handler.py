"""Auth handler class using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``QueryParam``, ``UserContext``, ``RequestCtx``) are
automatically extracted by ``_wrap_api_handler`` and responses are
returned as ``APIResponse`` objects.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Final

from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, QueryParam
from ai.backend.common.dto.manager.auth.request import (
    AuthorizeRequest,
    GetRoleRequest,
    SignoutRequest,
    SignupRequest,
    UpdateFullNameRequest,
    UpdatePasswordNoAuthRequest,
    UpdatePasswordRequest,
    UploadSSHKeypairRequest,
    VerifyAuthRequest,
)
from ai.backend.common.dto.manager.auth.response import (
    AuthorizeResponse,
    GetRoleResponse,
    GetSSHKeypairResponse,
    SignoutResponse,
    SignupResponse,
    SSHKeypairResponse,
    UpdateFullNameResponse,
    UpdatePasswordNoAuthResponse,
    UpdatePasswordResponse,
    VerifyAuthResponse,
)
from ai.backend.common.dto.manager.auth.types import (
    AuthResponseType,
    AuthSuccessResponse,
    AuthTokenType,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.errors.auth import AuthorizationFailed
from ai.backend.manager.services.auth.actions.authorize import AuthorizeAction
from ai.backend.manager.services.auth.actions.generate_ssh_keypair import GenerateSSHKeypairAction
from ai.backend.manager.services.auth.actions.get_role import GetRoleAction
from ai.backend.manager.services.auth.actions.get_ssh_keypair import GetSSHKeypairAction
from ai.backend.manager.services.auth.actions.signout import SignoutAction
from ai.backend.manager.services.auth.actions.signup import SignupAction
from ai.backend.manager.services.auth.actions.update_full_name import UpdateFullNameAction
from ai.backend.manager.services.auth.actions.update_password import UpdatePasswordAction
from ai.backend.manager.services.auth.actions.update_password_no_auth import (
    UpdatePasswordNoAuthAction,
)
from ai.backend.manager.services.auth.actions.upload_ssh_keypair import UploadSSHKeypairAction
from ai.backend.manager.services.processors import Processors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AuthHandler:
    """Auth API handler with constructor-injected dependencies."""

    def __init__(self, *, processors: Processors) -> None:
        self._processors = processors

    # ------------------------------------------------------------------
    # test_get (GET /auth, /auth/test)
    # ------------------------------------------------------------------

    async def test_get(self, ctx: UserContext) -> APIResponse:
        log.info("AUTH.TEST(ak:{})", ctx.access_key)
        resp = VerifyAuthResponse(authorized="yes", echo="")
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # test_post (POST /auth, /auth/test)
    # ------------------------------------------------------------------

    async def test_post(self, body: BodyParam[VerifyAuthRequest], ctx: UserContext) -> APIResponse:
        log.info("AUTH.TEST(ak:{})", ctx.access_key)
        params = body.parsed
        resp = VerifyAuthResponse(authorized="yes", echo=params.echo)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # get_role (GET /auth/role)
    # ------------------------------------------------------------------

    async def get_role(self, query: QueryParam[GetRoleRequest], ctx: UserContext) -> APIResponse:
        params = query.parsed
        log.info(
            "AUTH.ROLES(ak:{}, d:{}, g:{})",
            ctx.access_key,
            ctx.user_domain,
            params.group,
        )
        action = GetRoleAction(
            user_id=ctx.user_uuid,
            group_id=params.group,
            is_superadmin=ctx.is_superadmin,
            is_admin=ctx.is_admin,
        )
        result = await self._processors.auth.get_role.wait_for_complete(action)
        resp = GetRoleResponse(
            global_role=result.global_role,
            domain_role=result.domain_role,
            group_role=result.group_role,
        )
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # authorize (POST /auth/authorize)
    # ------------------------------------------------------------------

    async def authorize(
        self, body: BodyParam[AuthorizeRequest], ctx: RequestCtx
    ) -> APIResponse | web.StreamResponse:
        params = body.parsed
        log.info(
            "AUTH.AUTHORIZE(d:{}, u:{}, passwd:****, type:{})",
            params.domain,
            params.username,
            params.type,
        )
        action = AuthorizeAction(
            request=ctx.request,
            type=AuthTokenType(params.type),
            domain_name=params.domain,
            email=params.username,
            password=params.password,
            stoken=params.stoken,
        )
        result = await self._processors.auth.authorize.wait_for_complete(action)

        if result.stream_response is not None:
            return result.stream_response

        if result.authorization_result is None:
            raise AuthorizationFailed("Authorization result is missing")
        auth_result = result.authorization_result
        data = AuthSuccessResponse(
            response_type=AuthResponseType.SUCCESS,
            access_key=auth_result.access_key,
            secret_key=auth_result.secret_key,
            role=auth_result.role,
            status=auth_result.status,
        )
        resp = AuthorizeResponse(data=data)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # signup (POST /auth/signup)
    # ------------------------------------------------------------------

    async def signup(self, body: BodyParam[SignupRequest], ctx: RequestCtx) -> APIResponse:
        params = body.parsed
        log.info("AUTH.SIGNUP(d:{}, email:{}, passwd:****)", params.domain, params.email)
        action = SignupAction(
            request=ctx.request,
            domain_name=params.domain,
            email=params.email,
            password=params.password,
            username=params.username,
            full_name=params.full_name,
            description=params.description,
        )
        result = await self._processors.auth.signup.wait_for_complete(action)
        resp = SignupResponse(
            access_key=result.access_key,
            secret_key=result.secret_key,
        )
        return APIResponse.build(HTTPStatus.CREATED, resp)

    # ------------------------------------------------------------------
    # signout (POST /auth/signout)
    # ------------------------------------------------------------------

    async def signout(self, body: BodyParam[SignoutRequest], ctx: UserContext) -> APIResponse:
        params = body.parsed
        log.info("AUTH.SIGNOUT(d:{}, email:{})", ctx.user_domain, params.email)
        await self._processors.auth.signout.wait_for_complete(
            SignoutAction(
                user_id=ctx.user_uuid,
                domain_name=ctx.user_domain,
                requester_email=ctx.user_email,
                email=params.email,
                password=params.password,
            )
        )
        return APIResponse.build(HTTPStatus.OK, SignoutResponse())

    # ------------------------------------------------------------------
    # update_full_name (POST /auth/update-full-name)
    # ------------------------------------------------------------------

    async def update_full_name(
        self, body: BodyParam[UpdateFullNameRequest], ctx: UserContext
    ) -> APIResponse:
        params = body.parsed
        log.info("AUTH.UPDATE_FULL_NAME(d:{}, email:{})", ctx.user_domain, ctx.user_email)
        await self._processors.auth.update_full_name.wait_for_complete(
            UpdateFullNameAction(
                user_id=str(ctx.user_uuid),
                full_name=params.full_name,
                domain_name=ctx.user_domain,
                email=ctx.user_email,
            )
        )
        return APIResponse.build(HTTPStatus.OK, UpdateFullNameResponse())

    # ------------------------------------------------------------------
    # update_password (POST /auth/update-password)
    # ------------------------------------------------------------------

    async def update_password(
        self,
        body: BodyParam[UpdatePasswordRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        log.info("AUTH.UPDATE_PASSWORD(d:{}, email:{})", ctx.user_domain, ctx.user_email)
        action = UpdatePasswordAction(
            request=req.request,
            user_id=ctx.user_uuid,
            domain_name=ctx.user_domain,
            email=ctx.user_email,
            old_password=params.old_password,
            new_password=params.new_password,
            new_password_confirm=params.new_password2,
        )
        result = await self._processors.auth.update_password.wait_for_complete(action)
        if not result.success:
            resp = UpdatePasswordResponse(error_msg="new password mismatch")
            return APIResponse.build(HTTPStatus.BAD_REQUEST, resp)
        return APIResponse.build(HTTPStatus.OK, UpdatePasswordResponse())

    # ------------------------------------------------------------------
    # update_password_no_auth (POST /auth/update-password-no-auth)
    # ------------------------------------------------------------------

    async def update_password_no_auth(
        self, body: BodyParam[UpdatePasswordNoAuthRequest], ctx: RequestCtx
    ) -> APIResponse:
        params = body.parsed
        log.info(
            "AUTH.UPDATE_PASSWORD_NO_AUTH(d:{}, u:{}, passwd:****)",
            params.domain,
            params.username,
        )
        action = UpdatePasswordNoAuthAction(
            request=ctx.request,
            domain_name=params.domain,
            email=params.username,
            current_password=params.current_password,
            new_password=params.new_password,
        )
        result = await self._processors.auth.update_password_no_auth.wait_for_complete(action)
        resp = UpdatePasswordNoAuthResponse(
            password_changed_at=result.password_changed_at.isoformat(),
        )
        return APIResponse.build(HTTPStatus.CREATED, resp)

    # ------------------------------------------------------------------
    # get_ssh_keypair (GET /auth/ssh-keypair)
    # ------------------------------------------------------------------

    async def get_ssh_keypair(self, ctx: UserContext) -> APIResponse:
        log.info("AUTH.GET_SSH_KEYPAIR(d:{}, ak:{})", ctx.user_domain, ctx.access_key)
        result = await self._processors.auth.get_ssh_keypair.wait_for_complete(
            GetSSHKeypairAction(
                user_id=ctx.user_uuid,
                access_key=ctx.access_key,
            )
        )
        resp = GetSSHKeypairResponse(ssh_public_key=result.public_key)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # generate_ssh_keypair (PATCH /auth/ssh-keypair)
    # ------------------------------------------------------------------

    async def generate_ssh_keypair(self, ctx: UserContext) -> APIResponse:
        log.info("AUTH.REFRESH_SSH_KEYPAIR(d:{}, ak:{})", ctx.user_domain, ctx.access_key)
        result = await self._processors.auth.generate_ssh_keypair.wait_for_complete(
            GenerateSSHKeypairAction(
                user_id=ctx.user_uuid,
                access_key=ctx.access_key,
            )
        )
        resp = SSHKeypairResponse(
            ssh_public_key=result.ssh_keypair.ssh_public_key,
            ssh_private_key=result.ssh_keypair.ssh_private_key,
        )
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # upload_ssh_keypair (POST /auth/ssh-keypair)
    # ------------------------------------------------------------------

    async def upload_ssh_keypair(
        self, body: BodyParam[UploadSSHKeypairRequest], ctx: UserContext
    ) -> APIResponse:
        params = body.parsed
        pubkey = f"{params.pubkey.rstrip()}\n"
        privkey = f"{params.privkey.rstrip()}\n"
        log.info("AUTH.SAVE_SSH_KEYPAIR(d:{}, ak:{})", ctx.user_domain, ctx.access_key)
        result = await self._processors.auth.upload_ssh_keypair.wait_for_complete(
            UploadSSHKeypairAction(
                user_id=ctx.user_uuid,
                public_key=pubkey,
                private_key=privkey,
                access_key=ctx.access_key,
            )
        )
        resp = SSHKeypairResponse(
            ssh_public_key=result.ssh_keypair.ssh_public_key,
            ssh_private_key=result.ssh_keypair.ssh_private_key,
        )
        return APIResponse.build(HTTPStatus.OK, resp)
