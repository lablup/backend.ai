"""
Tests for AuthHandler methods (new-style auth module).

Each test verifies that the AuthHandler method correctly:
- Accepts typed parameters (BodyParam, QueryParam, UserContext, RequestCtx)
- Calls the appropriate processor action with correct arguments
- Returns the correct APIResponse with proper status codes

Note: Auth decorator tests (auth_required, admin_required, etc.) belong
in middleware tests, not here — AuthHandler methods assume the request
has already passed through auth_middleware.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web

from ai.backend.common.api_handlers import BodyParam, QueryParam
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
from ai.backend.manager.api.rest.auth.handler import AuthHandler
from ai.backend.manager.data.auth.types import AuthorizationResult, SSHKeypair
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.services.auth.actions.authorize import AuthorizeActionResult
from ai.backend.manager.services.auth.actions.generate_ssh_keypair import (
    GenerateSSHKeypairActionResult,
)
from ai.backend.manager.services.auth.actions.get_role import GetRoleActionResult
from ai.backend.manager.services.auth.actions.get_ssh_keypair import GetSSHKeypairActionResult
from ai.backend.manager.services.auth.actions.signout import SignoutActionResult
from ai.backend.manager.services.auth.actions.signup import SignupActionResult
from ai.backend.manager.services.auth.actions.update_full_name import UpdateFullNameActionResult
from ai.backend.manager.services.auth.actions.update_password import UpdatePasswordActionResult
from ai.backend.manager.services.auth.actions.update_password_no_auth import (
    UpdatePasswordNoAuthActionResult,
)
from ai.backend.manager.services.auth.actions.upload_ssh_keypair import UploadSSHKeypairActionResult

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_processors() -> MagicMock:
    """Mock Processors for AuthHandler constructor injection."""
    return MagicMock()


@pytest.fixture
def handler(mock_processors: MagicMock) -> AuthHandler:
    """AuthHandler instance with mock processors."""
    return AuthHandler(processors=mock_processors)


@pytest.fixture
def user_context() -> UserContext:
    """UserContext for authenticated endpoints."""
    return UserContext(
        user_uuid=uuid.uuid4(),
        user_email="test@example.com",
        user_domain="default",
        access_key="AKTEST",
        is_admin=False,
        is_superadmin=False,
    )


@pytest.fixture
def request_ctx() -> RequestCtx:
    """RequestCtx for endpoints needing raw request access."""
    return RequestCtx(request=MagicMock(spec=web.Request))


# ---------------------------------------------------------------------------
# Test Classes
# ---------------------------------------------------------------------------


class TestTestGet:
    """Tests for test_get handler (GET /auth)."""

    @pytest.mark.asyncio
    async def test_returns_authorized_yes(
        self,
        handler: AuthHandler,
        user_context: UserContext,
    ) -> None:
        """Verify test_get returns authorized=yes with empty echo."""
        response = await handler.test_get(user_context)

        assert response.status_code == HTTPStatus.OK
        data = response.to_json
        assert data is not None
        assert data["authorized"] == "yes"
        assert data["echo"] == ""


class TestTestPost:
    """Tests for test_post handler (POST /auth)."""

    @pytest.mark.asyncio
    async def test_returns_echo(
        self,
        handler: AuthHandler,
        user_context: UserContext,
    ) -> None:
        """Verify test_post returns echo from body."""
        body: BodyParam[VerifyAuthRequest] = BodyParam(VerifyAuthRequest)
        body.from_body({"echo": "hello"})

        response = await handler.test_post(body, user_context)

        assert response.status_code == HTTPStatus.OK
        data = response.to_json
        assert data is not None
        assert data["authorized"] == "yes"
        assert data["echo"] == "hello"


class TestAuthorize:
    """Tests for authorize handler (public endpoint)."""

    @pytest.fixture
    def authorize_result(self) -> AuthorizeActionResult:
        return AuthorizeActionResult(
            stream_response=None,
            authorization_result=AuthorizationResult(
                user_id=uuid.uuid4(),
                access_key="TESTKEY",
                secret_key="TESTSECRET",
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
            ),
        )

    @pytest.mark.asyncio
    async def test_calls_processor_and_returns_result(
        self,
        handler: AuthHandler,
        request_ctx: RequestCtx,
        mock_processors: MagicMock,
        authorize_result: AuthorizeActionResult,
    ) -> None:
        """Verify processor is called and authorization result is returned."""
        body: BodyParam[AuthorizeRequest] = BodyParam(AuthorizeRequest)
        body.from_body({
            "type": "keypair",
            "domain": "default",
            "username": "test@example.com",
            "password": "password123",
        })
        mock_processors.auth.authorize.wait_for_complete = AsyncMock(return_value=authorize_result)

        response = await handler.authorize(body, request_ctx)

        mock_processors.auth.authorize.wait_for_complete.assert_called_once()
        assert not isinstance(response, web.StreamResponse)
        assert response.status_code == HTTPStatus.OK
        assert authorize_result.authorization_result is not None
        data = response.to_json
        assert data is not None
        assert data["data"]["access_key"] == authorize_result.authorization_result.access_key
        assert data["data"]["secret_key"] == authorize_result.authorization_result.secret_key

    @pytest.mark.asyncio
    async def test_passes_params_to_action(
        self,
        handler: AuthHandler,
        request_ctx: RequestCtx,
        mock_processors: MagicMock,
        authorize_result: AuthorizeActionResult,
    ) -> None:
        """Verify domain, username, password are passed to Action."""
        domain = "test-domain"
        email = "user@example.com"
        password = "jwtpass"
        stoken = "session-token"
        body: BodyParam[AuthorizeRequest] = BodyParam(AuthorizeRequest)
        body.from_body({
            "type": "jwt",
            "domain": domain,
            "username": email,
            "password": password,
            "stoken": stoken,
        })
        mock_processors.auth.authorize.wait_for_complete = AsyncMock(return_value=authorize_result)

        await handler.authorize(body, request_ctx)

        action = mock_processors.auth.authorize.wait_for_complete.call_args[0][0]
        assert action.domain_name == domain
        assert action.email == email
        assert action.password == password
        assert action.stoken == stoken

    @pytest.mark.asyncio
    async def test_stream_response_passthrough(
        self,
        handler: AuthHandler,
        request_ctx: RequestCtx,
        mock_processors: MagicMock,
    ) -> None:
        """Verify StreamResponse from hook is passed through."""
        stream_resp = MagicMock(spec=web.StreamResponse)
        result = AuthorizeActionResult(
            stream_response=stream_resp,
            authorization_result=None,
        )
        body: BodyParam[AuthorizeRequest] = BodyParam(AuthorizeRequest)
        body.from_body({
            "type": "keypair",
            "domain": "default",
            "username": "test@example.com",
            "password": "pass",
        })
        mock_processors.auth.authorize.wait_for_complete = AsyncMock(return_value=result)

        response = await handler.authorize(body, request_ctx)

        assert response is stream_resp


class TestSignup:
    """Tests for signup handler (public endpoint)."""

    @pytest.fixture
    def signup_result(self) -> SignupActionResult:
        return SignupActionResult(
            user_id=uuid.uuid4(),
            access_key="NEWKEY",
            secret_key="NEWSECRET",
        )

    @pytest.mark.asyncio
    async def test_calls_processor_and_returns_created(
        self,
        handler: AuthHandler,
        request_ctx: RequestCtx,
        mock_processors: MagicMock,
        signup_result: SignupActionResult,
    ) -> None:
        """Verify processor is called and HTTP 201 CREATED is returned."""
        body: BodyParam[SignupRequest] = BodyParam(SignupRequest)
        body.from_body({
            "domain": "default",
            "email": "newuser@example.com",
            "password": "securepassword",
        })
        mock_processors.auth.signup.wait_for_complete = AsyncMock(return_value=signup_result)

        response = await handler.signup(body, request_ctx)

        mock_processors.auth.signup.wait_for_complete.assert_called_once()
        assert response.status_code == HTTPStatus.CREATED
        data = response.to_json
        assert data is not None
        assert data["access_key"] == signup_result.access_key
        assert data["secret_key"] == signup_result.secret_key

    @pytest.mark.asyncio
    async def test_passes_optional_params_to_action(
        self,
        handler: AuthHandler,
        request_ctx: RequestCtx,
        mock_processors: MagicMock,
        signup_result: SignupActionResult,
    ) -> None:
        """Verify optional params are passed to Action."""
        domain = "custom-domain"
        email = "fulluser@example.com"
        username = "fulluser"
        full_name = "Full Name"
        body: BodyParam[SignupRequest] = BodyParam(SignupRequest)
        body.from_body({
            "domain": domain,
            "email": email,
            "password": "password",
            "username": username,
            "full_name": full_name,
            "description": "Description",
        })
        mock_processors.auth.signup.wait_for_complete = AsyncMock(return_value=signup_result)

        await handler.signup(body, request_ctx)

        action = mock_processors.auth.signup.wait_for_complete.call_args[0][0]
        assert action.domain_name == domain
        assert action.email == email
        assert action.username == username
        assert action.full_name == full_name


class TestSignout:
    """Tests for signout handler."""

    @pytest.mark.asyncio
    async def test_calls_processor(
        self,
        handler: AuthHandler,
        user_context: UserContext,
        mock_processors: MagicMock,
    ) -> None:
        """Verify processor is called and empty response is returned."""
        email = "test@example.com"
        body: BodyParam[SignoutRequest] = BodyParam(SignoutRequest)
        body.from_body({"email": email, "password": "pass"})
        mock_processors.auth.signout.wait_for_complete = AsyncMock(
            return_value=SignoutActionResult(success=True)
        )

        response = await handler.signout(body, user_context)

        mock_processors.auth.signout.wait_for_complete.assert_called_once()
        action = mock_processors.auth.signout.wait_for_complete.call_args[0][0]
        assert action.user_id == user_context.user_uuid
        assert action.email == email
        assert response.status_code == HTTPStatus.OK


class TestGetRole:
    """Tests for get_role handler."""

    @pytest.mark.asyncio
    async def test_calls_processor_and_returns_roles(
        self,
        handler: AuthHandler,
        user_context: UserContext,
        mock_processors: MagicMock,
    ) -> None:
        """Verify processor is called and roles are returned."""
        global_role = "user"
        domain_role = "user"
        query: QueryParam[GetRoleRequest] = QueryParam(GetRoleRequest)
        query.from_query({})
        mock_processors.auth.get_role.wait_for_complete = AsyncMock(
            return_value=GetRoleActionResult(
                global_role=global_role,
                domain_role=domain_role,
                group_role=None,
            )
        )

        response = await handler.get_role(query, user_context)

        mock_processors.auth.get_role.wait_for_complete.assert_called_once()
        assert response.status_code == HTTPStatus.OK
        data = response.to_json
        assert data is not None
        assert data["global_role"] == global_role
        assert data["domain_role"] == domain_role
        assert data["group_role"] is None

    @pytest.mark.asyncio
    async def test_passes_group_to_action(
        self,
        handler: AuthHandler,
        user_context: UserContext,
        mock_processors: MagicMock,
    ) -> None:
        """Verify group parameter is passed to Action."""
        group_uuid = uuid.uuid4()
        query: QueryParam[GetRoleRequest] = QueryParam(GetRoleRequest)
        query.from_query({"group": str(group_uuid)})
        mock_processors.auth.get_role.wait_for_complete = AsyncMock(
            return_value=GetRoleActionResult(
                global_role="user",
                domain_role="user",
                group_role="member",
            )
        )

        await handler.get_role(query, user_context)

        action = mock_processors.auth.get_role.wait_for_complete.call_args[0][0]
        assert action.group_id == group_uuid

    @pytest.mark.asyncio
    async def test_uses_admin_flags_from_context(
        self,
        handler: AuthHandler,
        mock_processors: MagicMock,
    ) -> None:
        """Verify is_admin and is_superadmin are passed from UserContext."""
        admin_ctx = UserContext(
            user_uuid=uuid.uuid4(),
            user_email="admin@example.com",
            user_domain="default",
            access_key="AKADMIN",
            is_admin=True,
            is_superadmin=True,
        )
        query: QueryParam[GetRoleRequest] = QueryParam(GetRoleRequest)
        query.from_query({})
        mock_processors.auth.get_role.wait_for_complete = AsyncMock(
            return_value=GetRoleActionResult(
                global_role="superadmin",
                domain_role="admin",
                group_role=None,
            )
        )

        await handler.get_role(query, admin_ctx)

        action = mock_processors.auth.get_role.wait_for_complete.call_args[0][0]
        assert action.is_admin is True
        assert action.is_superadmin is True


class TestUpdatePassword:
    """Tests for update_password handler."""

    @pytest.mark.asyncio
    async def test_calls_processor_on_success(
        self,
        handler: AuthHandler,
        user_context: UserContext,
        request_ctx: RequestCtx,
        mock_processors: MagicMock,
    ) -> None:
        """Verify processor is called and OK is returned on success."""
        body: BodyParam[UpdatePasswordRequest] = BodyParam(UpdatePasswordRequest)
        body.from_body({
            "old_password": "oldpass",
            "new_password": "newpass",
            "new_password2": "newpass",
        })
        mock_processors.auth.update_password.wait_for_complete = AsyncMock(
            return_value=UpdatePasswordActionResult(success=True, message="OK")
        )

        response = await handler.update_password(body, user_context, request_ctx)

        mock_processors.auth.update_password.wait_for_complete.assert_called_once()
        assert response.status_code == HTTPStatus.OK

    @pytest.mark.asyncio
    async def test_returns_bad_request_on_failure(
        self,
        handler: AuthHandler,
        user_context: UserContext,
        request_ctx: RequestCtx,
        mock_processors: MagicMock,
    ) -> None:
        """Verify BAD_REQUEST is returned when password update fails."""
        body: BodyParam[UpdatePasswordRequest] = BodyParam(UpdatePasswordRequest)
        body.from_body({
            "old_password": "oldpass",
            "new_password": "newpass",
            "new_password2": "differentpass",
        })
        mock_processors.auth.update_password.wait_for_complete = AsyncMock(
            return_value=UpdatePasswordActionResult(success=False, message="mismatch")
        )

        response = await handler.update_password(body, user_context, request_ctx)

        assert response.status_code == HTTPStatus.BAD_REQUEST


class TestUpdatePasswordNoAuth:
    """Tests for update_password_no_auth handler (public endpoint)."""

    @pytest.mark.asyncio
    async def test_calls_processor_and_returns_created(
        self,
        handler: AuthHandler,
        request_ctx: RequestCtx,
        mock_processors: MagicMock,
    ) -> None:
        """Verify processor is called and HTTP 201 CREATED is returned."""
        password_changed_at = datetime.now(tz=UTC)
        body: BodyParam[UpdatePasswordNoAuthRequest] = BodyParam(UpdatePasswordNoAuthRequest)
        body.from_body({
            "domain": "default",
            "username": "user@example.com",
            "current_password": "current",
            "new_password": "newpass",
        })
        mock_processors.auth.update_password_no_auth.wait_for_complete = AsyncMock(
            return_value=UpdatePasswordNoAuthActionResult(
                user_id=uuid.uuid4(),
                password_changed_at=password_changed_at,
            )
        )

        response = await handler.update_password_no_auth(body, request_ctx)

        mock_processors.auth.update_password_no_auth.wait_for_complete.assert_called_once()
        assert response.status_code == HTTPStatus.CREATED
        data = response.to_json
        assert data is not None
        assert "password_changed_at" in data


class TestUpdateFullName:
    """Tests for update_full_name handler."""

    @pytest.mark.asyncio
    async def test_calls_processor(
        self,
        handler: AuthHandler,
        user_context: UserContext,
        mock_processors: MagicMock,
    ) -> None:
        """Verify processor is called with correct params."""
        full_name = "New Name"
        body: BodyParam[UpdateFullNameRequest] = BodyParam(UpdateFullNameRequest)
        body.from_body({"email": "user@example.com", "full_name": full_name})
        mock_processors.auth.update_full_name.wait_for_complete = AsyncMock(
            return_value=UpdateFullNameActionResult(success=True)
        )

        response = await handler.update_full_name(body, user_context)

        mock_processors.auth.update_full_name.wait_for_complete.assert_called_once()
        action = mock_processors.auth.update_full_name.wait_for_complete.call_args[0][0]
        assert action.full_name == full_name
        assert response.status_code == HTTPStatus.OK


class TestGetSSHKeypair:
    """Tests for get_ssh_keypair handler."""

    @pytest.mark.asyncio
    async def test_calls_processor_and_returns_public_key(
        self,
        handler: AuthHandler,
        user_context: UserContext,
        mock_processors: MagicMock,
    ) -> None:
        """Verify processor is called and public key is returned."""
        public_key = "ssh-rsa AAAAB3...\n"
        mock_processors.auth.get_ssh_keypair.wait_for_complete = AsyncMock(
            return_value=GetSSHKeypairActionResult(public_key=public_key)
        )

        response = await handler.get_ssh_keypair(user_context)

        mock_processors.auth.get_ssh_keypair.wait_for_complete.assert_called_once()
        assert response.status_code == HTTPStatus.OK
        data = response.to_json
        assert data is not None
        assert data["ssh_public_key"] == public_key


class TestGenerateSSHKeypair:
    """Tests for generate_ssh_keypair handler."""

    @pytest.mark.asyncio
    async def test_calls_processor_and_returns_keypair(
        self,
        handler: AuthHandler,
        user_context: UserContext,
        mock_processors: MagicMock,
    ) -> None:
        """Verify processor is called and keypair is returned."""
        ssh_public_key = "ssh-rsa NEWPUB...\n"
        ssh_private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n"
        mock_processors.auth.generate_ssh_keypair.wait_for_complete = AsyncMock(
            return_value=GenerateSSHKeypairActionResult(
                ssh_keypair=SSHKeypair(
                    ssh_public_key=ssh_public_key,
                    ssh_private_key=ssh_private_key,
                )
            )
        )

        response = await handler.generate_ssh_keypair(user_context)

        mock_processors.auth.generate_ssh_keypair.wait_for_complete.assert_called_once()
        assert response.status_code == HTTPStatus.OK
        data = response.to_json
        assert data is not None
        assert data["ssh_public_key"] == ssh_public_key
        assert data["ssh_private_key"] == ssh_private_key


class TestUploadSSHKeypair:
    """Tests for upload_ssh_keypair handler."""

    @pytest.mark.asyncio
    async def test_calls_processor_and_returns_keypair(
        self,
        handler: AuthHandler,
        user_context: UserContext,
        mock_processors: MagicMock,
    ) -> None:
        """Verify processor is called and keypair is returned."""
        body: BodyParam[UploadSSHKeypairRequest] = BodyParam(UploadSSHKeypairRequest)
        body.from_body({
            "pubkey": "ssh-rsa AAAAB3...",
            "privkey": "-----BEGIN RSA PRIVATE KEY-----\n...",
        })
        mock_processors.auth.upload_ssh_keypair.wait_for_complete = AsyncMock(
            return_value=UploadSSHKeypairActionResult(
                ssh_keypair=SSHKeypair(
                    ssh_public_key="ssh-rsa AAAAB3...\n",
                    ssh_private_key="-----BEGIN RSA PRIVATE KEY-----\n...\n",
                )
            )
        )

        response = await handler.upload_ssh_keypair(body, user_context)

        mock_processors.auth.upload_ssh_keypair.wait_for_complete.assert_called_once()
        assert response.status_code == HTTPStatus.OK
        data = response.to_json
        assert data is not None
        assert "ssh_public_key" in data
        assert "ssh_private_key" in data
