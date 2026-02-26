"""Auth handler class using constructor dependency injection.

All 11 unique handlers from the legacy ``api/auth.py`` are migrated here
as methods of ``AuthHandler``, using Pydantic DTOs for request validation
and ``APIResponse.build()`` for response serialization.

Handlers are registered as standard aiohttp request handlers (accepting
``web.Request``) so that they retain access to per-request auth state
(``request["user"]``, ``request["keypair"]``, etc.) set by
``auth_middleware``.
"""

from __future__ import annotations

import json
import logging
from http import HTTPStatus
from typing import Any, Final

from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BaseRequestModel, BodyParam, QueryParam
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
from ai.backend.manager.errors.api import InvalidAPIParameters
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


def _parse_body[T: BaseRequestModel](request_body: dict[str, Any], model: type[T]) -> BodyParam[T]:
    """Parse a JSON body into a BodyParam with the given Pydantic model."""
    bp: BodyParam[T] = BodyParam(model)
    bp.from_body(request_body)
    return bp


async def _read_json_body(request: web.Request) -> dict[str, Any]:
    """Read and parse JSON body from the request."""
    try:
        result: dict[str, Any] = await request.json()
        return result
    except json.JSONDecodeError as e:
        raise InvalidAPIParameters("Malformed request body") from e


class AuthHandler:
    """Auth API handler with constructor-injected dependencies."""

    def __init__(self, *, processors: Processors) -> None:
        self._processors = processors

    # ------------------------------------------------------------------
    # test (GET/POST /auth, /auth/test)
    # ------------------------------------------------------------------

    async def test(self, request: web.Request) -> web.Response:
        log.info("AUTH.TEST(ak:{})", request["keypair"]["access_key"])
        body = await _read_json_body(request)
        params = _parse_body(body, VerifyAuthRequest).parsed
        resp = VerifyAuthResponse(authorized="yes", echo=params.echo)
        return web.json_response(
            APIResponse.build(HTTPStatus.OK, resp).to_json,
            status=HTTPStatus.OK,
        )

    # ------------------------------------------------------------------
    # get_role (GET /auth/role)
    # ------------------------------------------------------------------

    async def get_role(self, request: web.Request) -> web.Response:
        qp = QueryParam(GetRoleRequest)
        qp.from_query(request.query)
        params = qp.parsed
        log.info(
            "AUTH.ROLES(ak:{}, d:{}, g:{})",
            request["keypair"]["access_key"],
            request["user"]["domain_name"],
            params.group,
        )
        action = GetRoleAction(
            user_id=request["user"]["uuid"],
            group_id=params.group,
            is_superadmin=request["is_superadmin"],
            is_admin=request["is_admin"],
        )
        result = await self._processors.auth.get_role.wait_for_complete(action)
        resp = GetRoleResponse(
            global_role=result.global_role,
            domain_role=result.domain_role,
            group_role=result.group_role,
        )
        return web.json_response(
            APIResponse.build(HTTPStatus.OK, resp).to_json,
            status=HTTPStatus.OK,
        )

    # ------------------------------------------------------------------
    # authorize (POST /auth/authorize)
    # ------------------------------------------------------------------

    async def authorize(self, request: web.Request) -> web.StreamResponse:
        body = await _read_json_body(request)
        params = _parse_body(body, AuthorizeRequest).parsed
        log.info(
            "AUTH.AUTHORIZE(d:{}, u:{}, passwd:****, type:{})",
            params.domain,
            params.username,
            params.type,
        )
        action = AuthorizeAction(
            request=request,
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
        return web.json_response(
            APIResponse.build(HTTPStatus.OK, resp).to_json,
            status=HTTPStatus.OK,
        )

    # ------------------------------------------------------------------
    # signup (POST /auth/signup)
    # ------------------------------------------------------------------

    async def signup(self, request: web.Request) -> web.Response:
        body = await _read_json_body(request)
        params = _parse_body(body, SignupRequest).parsed
        log.info("AUTH.SIGNUP(d:{}, email:{}, passwd:****)", params.domain, params.email)
        action = SignupAction(
            request=request,
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
        return web.json_response(
            APIResponse.build(HTTPStatus.CREATED, resp).to_json,
            status=HTTPStatus.CREATED,
        )

    # ------------------------------------------------------------------
    # signout (POST /auth/signout)
    # ------------------------------------------------------------------

    async def signout(self, request: web.Request) -> web.Response:
        body = await _read_json_body(request)
        params = _parse_body(body, SignoutRequest).parsed
        domain_name = request["user"]["domain_name"]
        log.info("AUTH.SIGNOUT(d:{}, email:{})", domain_name, params.email)
        await self._processors.auth.signout.wait_for_complete(
            SignoutAction(
                user_id=request["user"]["uuid"],
                domain_name=domain_name,
                requester_email=request["user"]["email"],
                email=params.email,
                password=params.password,
            )
        )
        return web.json_response(
            APIResponse.build(HTTPStatus.OK, SignoutResponse()).to_json,
            status=HTTPStatus.OK,
        )

    # ------------------------------------------------------------------
    # update_full_name (POST /auth/update-full-name)
    # ------------------------------------------------------------------

    async def update_full_name(self, request: web.Request) -> web.Response:
        body = await _read_json_body(request)
        params = _parse_body(body, UpdateFullNameRequest).parsed
        domain_name = request["user"]["domain_name"]
        email = request["user"]["email"]
        log.info("AUTH.UPDATE_FULL_NAME(d:{}, email:{})", domain_name, email)
        await self._processors.auth.update_full_name.wait_for_complete(
            UpdateFullNameAction(
                user_id=request["user"]["uuid"],
                full_name=params.full_name,
                domain_name=domain_name,
                email=email,
            )
        )
        return web.json_response(
            APIResponse.build(HTTPStatus.OK, UpdateFullNameResponse()).to_json,
            status=HTTPStatus.OK,
        )

    # ------------------------------------------------------------------
    # update_password (POST /auth/update-password)
    # ------------------------------------------------------------------

    async def update_password(self, request: web.Request) -> web.Response:
        body = await _read_json_body(request)
        params = _parse_body(body, UpdatePasswordRequest).parsed
        domain_name = request["user"]["domain_name"]
        email = request["user"]["email"]
        log.info("AUTH.UPDATE_PASSWORD(d:{}, email:{})", domain_name, email)
        action = UpdatePasswordAction(
            request=request,
            user_id=request["user"]["uuid"],
            domain_name=domain_name,
            email=email,
            old_password=params.old_password,
            new_password=params.new_password,
            new_password_confirm=params.new_password2,
        )
        result = await self._processors.auth.update_password.wait_for_complete(action)
        if not result.success:
            resp = UpdatePasswordResponse(error_msg="new password mismatch")
            return web.json_response(
                APIResponse.build(HTTPStatus.BAD_REQUEST, resp).to_json,
                status=HTTPStatus.BAD_REQUEST,
            )
        return web.json_response(
            APIResponse.build(HTTPStatus.OK, UpdatePasswordResponse()).to_json,
            status=HTTPStatus.OK,
        )

    # ------------------------------------------------------------------
    # update_password_no_auth (POST /auth/update-password-no-auth)
    # ------------------------------------------------------------------

    async def update_password_no_auth(self, request: web.Request) -> web.Response:
        body = await _read_json_body(request)
        params = _parse_body(body, UpdatePasswordNoAuthRequest).parsed
        log.info(
            "AUTH.UPDATE_PASSWORD_NO_AUTH(d:{}, u:{}, passwd:****)",
            params.domain,
            params.username,
        )
        action = UpdatePasswordNoAuthAction(
            request=request,
            domain_name=params.domain,
            email=params.username,
            current_password=params.current_password,
            new_password=params.new_password,
        )
        result = await self._processors.auth.update_password_no_auth.wait_for_complete(action)
        resp = UpdatePasswordNoAuthResponse(
            password_changed_at=result.password_changed_at.isoformat(),
        )
        return web.json_response(
            APIResponse.build(HTTPStatus.CREATED, resp).to_json,
            status=HTTPStatus.CREATED,
        )

    # ------------------------------------------------------------------
    # get_ssh_keypair (GET /auth/ssh-keypair)
    # ------------------------------------------------------------------

    async def get_ssh_keypair(self, request: web.Request) -> web.Response:
        domain_name = request["user"]["domain_name"]
        access_key = request["keypair"]["access_key"]
        log.info("AUTH.GET_SSH_KEYPAIR(d:{}, ak:{})", domain_name, access_key)
        result = await self._processors.auth.get_ssh_keypair.wait_for_complete(
            GetSSHKeypairAction(
                user_id=request["user"]["uuid"],
                access_key=access_key,
            )
        )
        resp = GetSSHKeypairResponse(ssh_public_key=result.public_key)
        return web.json_response(
            APIResponse.build(HTTPStatus.OK, resp).to_json,
            status=HTTPStatus.OK,
        )

    # ------------------------------------------------------------------
    # generate_ssh_keypair (PATCH /auth/ssh-keypair)
    # ------------------------------------------------------------------

    async def generate_ssh_keypair(self, request: web.Request) -> web.Response:
        domain_name = request["user"]["domain_name"]
        access_key = request["keypair"]["access_key"]
        log.info("AUTH.REFRESH_SSH_KEYPAIR(d:{}, ak:{})", domain_name, access_key)
        result = await self._processors.auth.generate_ssh_keypair.wait_for_complete(
            GenerateSSHKeypairAction(
                user_id=request["user"]["uuid"],
                access_key=access_key,
            )
        )
        resp = SSHKeypairResponse(
            ssh_public_key=result.ssh_keypair.ssh_public_key,
            ssh_private_key=result.ssh_keypair.ssh_private_key,
        )
        return web.json_response(
            APIResponse.build(HTTPStatus.OK, resp).to_json,
            status=HTTPStatus.OK,
        )

    # ------------------------------------------------------------------
    # upload_ssh_keypair (POST /auth/ssh-keypair)
    # ------------------------------------------------------------------

    async def upload_ssh_keypair(self, request: web.Request) -> web.Response:
        body = await _read_json_body(request)
        params = _parse_body(body, UploadSSHKeypairRequest).parsed
        domain_name = request["user"]["domain_name"]
        access_key = request["keypair"]["access_key"]
        pubkey = f"{params.pubkey.rstrip()}\n"
        privkey = f"{params.privkey.rstrip()}\n"
        log.info("AUTH.SAVE_SSH_KEYPAIR(d:{}, ak:{})", domain_name, access_key)
        result = await self._processors.auth.upload_ssh_keypair.wait_for_complete(
            UploadSSHKeypairAction(
                user_id=request["user"]["uuid"],
                public_key=pubkey,
                private_key=privkey,
                access_key=access_key,
            )
        )
        resp = SSHKeypairResponse(
            ssh_public_key=result.ssh_keypair.ssh_public_key,
            ssh_private_key=result.ssh_keypair.ssh_private_key,
        )
        return web.json_response(
            APIResponse.build(HTTPStatus.OK, resp).to_json,
            status=HTTPStatus.OK,
        )
