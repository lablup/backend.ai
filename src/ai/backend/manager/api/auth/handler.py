"""
REST API handlers for auth system.
Provides endpoints for authentication, user management, and SSH keypair operations.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Final

from aiohttp import web

from ai.backend.common.api_handlers import (
    APIResponse,
    BaseResponseModel,
    BodyParam,
    QueryParam,
    api_handler,
)
from ai.backend.common.dto.manager.auth.request import (
    AuthorizeRequest,
    GetRoleRequest,
    SignoutRequest,
    SignupRequest,
    UpdateFullNameRequest,
    UpdatePasswordNoAuthRequest,
    UpdatePasswordRequest,
    UploadSSHKeypairRequest,
)
from ai.backend.common.dto.manager.auth.response import (
    SignoutResponse,
    UpdateFullNameResponse,
    UpdatePasswordResponse,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import ProcessorsCtx, RequestCtx, UserContext
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

from . import auth_required_for_method
from .adapter import AuthAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

__all__ = ("AuthAPIHandler",)


class AuthAPIHandler:
    """REST API handler class for auth operations."""

    def __init__(self) -> None:
        self.adapter = AuthAdapter()

    # Test endpoint

    @auth_required_for_method
    @api_handler
    async def test(
        self,
        user_ctx: UserContext,
    ) -> APIResponse:
        """Test authentication."""
        log.info("AUTH.TEST(ak:{})", user_ctx.access_key)
        # Note: echo parameter handling requires QueryParam, but test endpoint
        # is simple enough to just return authorized status

        class TestResponse(BaseResponseModel):
            authorized: str

        return APIResponse.build(
            status_code=HTTPStatus.OK, response_model=TestResponse(authorized="yes")
        )

    # Authorization endpoints

    async def authorize(
        self,
        request: web.Request,
    ) -> web.StreamResponse:
        """Authorize a user with domain, username, and password.

        Note: This endpoint doesn't use @api_handler because it may return
        a streaming response for 2FA flows.
        """
        from ai.backend.manager.api.context import RootContext

        # Parse request body with pydantic validation
        body = await request.json()
        req = AuthorizeRequest.model_validate(body)

        root_ctx: RootContext = request.app["_root.context"]
        processors = root_ctx.processors

        log.info(
            "AUTH.AUTHORIZE(d:{}, u:{}, passwd:****, type:{})",
            req.domain,
            req.username,
            req.type,
        )

        action = AuthorizeAction(
            request=request,
            type=req.type,
            domain_name=req.domain,
            email=req.username,
            password=req.password,
            stoken=req.stoken,
        )
        result = await processors.auth.authorize.wait_for_complete(action)

        # Handle streaming response (for 2FA flows)
        if result.stream_response is not None:
            return result.stream_response

        if result.authorization_result is None:
            raise AuthorizationFailed("Authorization result is missing")

        resp = self.adapter.convert_authorize_result(result)
        return web.json_response(resp.model_dump(mode="json"), status=HTTPStatus.OK)

    @auth_required_for_method
    @api_handler
    async def get_role(
        self,
        query: QueryParam[GetRoleRequest],
        user_ctx: UserContext,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get user's role information."""
        req = query.parsed
        processors = processors_ctx.processors
        log.info(
            "AUTH.ROLES(ak:{}, d:{}, g:{})",
            user_ctx.access_key,
            user_ctx.user_domain,
            req.group,
        )

        # Get is_superadmin and is_admin from request context
        # These are set by auth middleware
        action = GetRoleAction(
            user_id=user_ctx.user_uuid,
            group_id=req.group,
            is_superadmin=False,  # Will be determined by service
            is_admin=False,  # Will be determined by service
        )
        result = await processors.auth.get_role.wait_for_complete(action)

        resp = self.adapter.convert_get_role_result(result)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @api_handler
    async def signup(
        self,
        body: BodyParam[SignupRequest],
        request_ctx: RequestCtx,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Sign up a new user."""
        req = body.parsed
        processors = processors_ctx.processors
        log.info("AUTH.SIGNUP(d:{}, email:{}, passwd:****)", req.domain, req.email)

        action = SignupAction(
            request=request_ctx.request,
            domain_name=req.domain,
            email=req.email,
            password=req.password,
            username=req.username,
            full_name=req.full_name,
            description=req.description,
        )
        result = await processors.auth.signup.wait_for_complete(action)

        resp = self.adapter.convert_signup_result(result)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def signout(
        self,
        body: BodyParam[SignoutRequest],
        user_ctx: UserContext,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Sign out a user."""
        req = body.parsed
        processors = processors_ctx.processors
        log.info("AUTH.SIGNOUT(d:{}, email:{})", user_ctx.user_domain, req.email)

        action = SignoutAction(
            user_id=user_ctx.user_uuid,
            domain_name=user_ctx.user_domain,
            requester_email=user_ctx.user_email,
            email=req.email,  # type: ignore  # validated by model
            password=req.password,
        )
        await processors.auth.signout.wait_for_complete(action)

        return APIResponse.build(status_code=HTTPStatus.OK, response_model=SignoutResponse())

    # Password management endpoints

    @auth_required_for_method
    @api_handler
    async def update_password(
        self,
        body: BodyParam[UpdatePasswordRequest],
        request_ctx: RequestCtx,
        user_ctx: UserContext,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Update user's password (requires authentication)."""
        req = body.parsed
        processors = processors_ctx.processors
        log.info("AUTH.UPDATE_PASSWORD(d:{}, email:{})", user_ctx.user_domain, user_ctx.user_email)

        action = UpdatePasswordAction(
            request=request_ctx.request,
            user_id=user_ctx.user_uuid,
            domain_name=user_ctx.user_domain,
            email=user_ctx.user_email,
            old_password=req.old_password,
            new_password=req.new_password,
            new_password_confirm=req.new_password2,
        )
        result = await processors.auth.update_password.wait_for_complete(action)

        if not result.success:
            return APIResponse.build(
                status_code=HTTPStatus.BAD_REQUEST,
                response_model=UpdatePasswordResponse(error_msg="new password mismatch"),
            )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=UpdatePasswordResponse())

    @api_handler
    async def update_password_no_auth(
        self,
        body: BodyParam[UpdatePasswordNoAuthRequest],
        request_ctx: RequestCtx,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Update user's password without authentication (for expired passwords)."""
        req = body.parsed
        processors = processors_ctx.processors
        log.info(
            "AUTH.UPDATE_PASSWORD_NO_AUTH(d:{}, u:{}, passwd:****)",
            req.domain,
            req.username,
        )

        action = UpdatePasswordNoAuthAction(
            request=request_ctx.request,
            domain_name=req.domain,
            email=req.username,
            current_password=req.current_password,
            new_password=req.new_password,
        )
        result = await processors.auth.update_password_no_auth.wait_for_complete(action)

        resp = self.adapter.convert_update_password_no_auth_result(result)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def update_full_name(
        self,
        body: BodyParam[UpdateFullNameRequest],
        user_ctx: UserContext,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Update user's full name."""
        req = body.parsed
        processors = processors_ctx.processors
        log.info("AUTH.UPDATE_FULL_NAME(d:{}, email:{})", user_ctx.user_domain, user_ctx.user_email)

        action = UpdateFullNameAction(
            user_id=str(user_ctx.user_uuid),
            full_name=req.full_name,
            domain_name=user_ctx.user_domain,
            email=user_ctx.user_email,
        )
        await processors.auth.update_full_name.wait_for_complete(action)

        return APIResponse.build(status_code=HTTPStatus.OK, response_model=UpdateFullNameResponse())

    # SSH keypair endpoints

    @auth_required_for_method
    @api_handler
    async def get_ssh_keypair(
        self,
        user_ctx: UserContext,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get user's SSH public key."""
        processors = processors_ctx.processors
        log.info("AUTH.GET_SSH_KEYPAIR(d:{}, ak:{})", user_ctx.user_domain, user_ctx.access_key)

        action = GetSSHKeypairAction(
            user_id=user_ctx.user_uuid,
            access_key=user_ctx.access_key,
        )
        result = await processors.auth.get_ssh_keypair.wait_for_complete(action)

        resp = self.adapter.convert_get_ssh_keypair_result(result)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def generate_ssh_keypair(
        self,
        user_ctx: UserContext,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Generate a new SSH keypair for the user."""
        processors = processors_ctx.processors
        log.info("AUTH.REFRESH_SSH_KEYPAIR(d:{}, ak:{})", user_ctx.user_domain, user_ctx.access_key)

        action = GenerateSSHKeypairAction(
            user_id=user_ctx.user_uuid,
            access_key=user_ctx.access_key,
        )
        result = await processors.auth.generate_ssh_keypair.wait_for_complete(action)

        resp = self.adapter.convert_generate_ssh_keypair_result(result)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def upload_ssh_keypair(
        self,
        body: BodyParam[UploadSSHKeypairRequest],
        user_ctx: UserContext,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Upload a custom SSH keypair."""
        req = body.parsed
        processors = processors_ctx.processors
        log.info("AUTH.SAVE_SSH_KEYPAIR(d:{}, ak:{})", user_ctx.user_domain, user_ctx.access_key)

        # Normalize keypair format (ensure trailing newline)
        pubkey = f"{req.pubkey.rstrip()}\n"
        privkey = f"{req.privkey.rstrip()}\n"

        action = UploadSSHKeypairAction(
            user_id=user_ctx.user_uuid,
            public_key=pubkey,
            private_key=privkey,
            access_key=user_ctx.access_key,
        )
        result = await processors.auth.upload_ssh_keypair.wait_for_complete(action)

        resp = self.adapter.convert_upload_ssh_keypair_result(result)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)
