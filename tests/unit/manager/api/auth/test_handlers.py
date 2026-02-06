"""
Tests for AuthAPIHandler business logic.

Focuses on handler-level logic that regression tests cannot cover:
- Full round-trip: request → action construction → result → response mapping
- Branching logic (success/failure paths, stream vs JSON response)
- Input normalization (e.g., trailing newline for SSH keys)
- Identity source verification (user_ctx vs request body)
- auth_required rejection
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web
from aiohttp.typedefs import Handler

from ai.backend.manager.api.auth import AuthAPIHandler
from ai.backend.manager.data.auth.types import AuthorizationResult, SSHKeypair
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
# Constants
# ---------------------------------------------------------------------------

USER_EMAIL = "test@example.com"
USER_DOMAIN = "default"
ACCESS_KEY = "TESTKEY123"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def handler() -> AuthAPIHandler:
    return AuthAPIHandler()


@pytest.fixture
def mock_root_ctx() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_processors(mock_root_ctx: MagicMock) -> MagicMock:
    processors: MagicMock = mock_root_ctx.processors
    return processors


@pytest.fixture
def user_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_user_data(user_uuid: uuid.UUID) -> dict[str, Any]:
    return {
        "uuid": user_uuid,
        "email": USER_EMAIL,
        "domain_name": USER_DOMAIN,
    }


@pytest.fixture
def mock_keypair_data() -> dict[str, Any]:
    return {"access_key": ACCESS_KEY}


@pytest.fixture
def create_app(
    handler: AuthAPIHandler,
    mock_root_ctx: MagicMock,
    mock_user_data: dict[str, Any],
    mock_keypair_data: dict[str, Any],
) -> Any:
    def _create(*, is_authorized: bool = True) -> web.Application:
        @web.middleware
        async def auth_mw(request: web.Request, handler: Handler) -> web.StreamResponse:
            request["user"] = mock_user_data
            request["keypair"] = mock_keypair_data
            request["is_authorized"] = is_authorized
            request["is_admin"] = False
            request["is_superadmin"] = False
            return await handler(request)

        app = web.Application(middlewares=[auth_mw])
        app["_root.context"] = mock_root_ctx
        app.router.add_get("/auth/test", handler.verify_auth)
        app.router.add_post("/auth/authorize", handler.authorize)
        app.router.add_post("/auth/signup", handler.signup)
        app.router.add_post("/auth/signout", handler.signout)
        app.router.add_post("/auth/password", handler.update_password)
        app.router.add_post("/auth/password-no-auth", handler.update_password_no_auth)
        app.router.add_post("/auth/full-name", handler.update_full_name)
        app.router.add_get("/auth/role", handler.get_role)
        app.router.add_get("/auth/ssh-keypair", handler.get_ssh_keypair)
        app.router.add_patch("/auth/ssh-keypair", handler.generate_ssh_keypair)
        app.router.add_post("/auth/ssh-keypair/upload", handler.upload_ssh_keypair)
        return app

    return _create


@pytest.fixture
def app(create_app: Any) -> web.Application:
    result: web.Application = create_app()
    return result


@pytest.fixture
async def client(aiohttp_client: Any, app: web.Application) -> Any:
    return await aiohttp_client(app)


class TestVerifyAuth:
    """Test verify_auth: echo round-trip and auth gating."""

    @pytest.mark.asyncio
    async def test_echoes_input(
        self,
        client: Any,
    ) -> None:
        """Authorized request returns echo string and authorized=yes."""
        echo_value = "hello-world"
        resp = await client.get("/auth/test", params={"echo": echo_value})

        assert resp.status == HTTPStatus.OK
        data = await resp.json()
        assert data["authorized"] == "yes"
        assert data["echo"] == echo_value

    @pytest.mark.asyncio
    async def test_rejects_unauthorized(
        self,
        aiohttp_client: Any,
        create_app: Any,
    ) -> None:
        """Unauthenticated request is rejected by auth_required."""
        app = create_app(is_authorized=False)
        client = await aiohttp_client(app)
        resp = await client.get("/auth/test", params={"echo": "test"})

        assert resp.status == HTTPStatus.UNAUTHORIZED


class TestAuthorize:
    """Test authorize handler: action construction, branching, and response mapping."""

    @pytest.mark.asyncio
    async def test_keypair_auth_round_trip(
        self,
        client: Any,
        mock_processors: MagicMock,
    ) -> None:
        """Full round-trip: request fields → action → AuthorizationResult → response JSON."""
        request_domain = "my-domain"
        request_email = "user@test.com"
        request_password = "secret123"
        request_stoken = "session-tok"
        result_access_key = "AK_FROM_RESULT"
        result_secret_key = "SK_FROM_RESULT"

        auth_result = AuthorizationResult(
            user_id=uuid.uuid4(),
            access_key=result_access_key,
            secret_key=result_secret_key,
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        result = AuthorizeActionResult(
            stream_response=None,
            authorization_result=auth_result,
        )
        mock_processors.auth.authorize.wait_for_complete = AsyncMock(return_value=result)

        resp = await client.post(
            "/auth/authorize",
            json={
                "type": "keypair",
                "domain": request_domain,
                "username": request_email,
                "password": request_password,
                "stoken": request_stoken,
            },
        )

        action = mock_processors.auth.authorize.wait_for_complete.call_args[0][0]
        assert action.domain_name == request_domain
        assert action.email == request_email
        assert action.password == request_password
        assert action.stoken == request_stoken

        assert resp.status == HTTPStatus.OK
        data = await resp.json()
        assert data["data"]["access_key"] == result_access_key
        assert data["data"]["secret_key"] == result_secret_key
        assert data["data"]["role"] == auth_result.role
        assert data["data"]["status"] == auth_result.status

    @pytest.mark.asyncio
    async def test_stream_response_bypasses_result_mapping(
        self,
        client: Any,
        mock_processors: MagicMock,
    ) -> None:
        """When stream_response is set, it is returned directly without result mapping."""
        jwt_token = "jwt-token-value"
        stream_resp = web.json_response({"token": jwt_token})
        result = AuthorizeActionResult(
            stream_response=stream_resp,
            authorization_result=None,
        )
        mock_processors.auth.authorize.wait_for_complete = AsyncMock(return_value=result)

        resp = await client.post(
            "/auth/authorize",
            json={
                "type": "jwt",
                "domain": USER_DOMAIN,
                "username": USER_EMAIL,
                "password": "pw",
            },
        )

        assert resp.status == HTTPStatus.OK
        data = await resp.json()
        assert data["token"] == jwt_token
        assert "data" not in data

    @pytest.mark.asyncio
    async def test_raises_when_both_none(
        self,
        client: Any,
        mock_processors: MagicMock,
    ) -> None:
        """When both stream_response and authorization_result are None, returns 401."""
        result = AuthorizeActionResult(
            stream_response=None,
            authorization_result=None,
        )
        mock_processors.auth.authorize.wait_for_complete = AsyncMock(return_value=result)

        resp = await client.post(
            "/auth/authorize",
            json={
                "type": "keypair",
                "domain": USER_DOMAIN,
                "username": USER_EMAIL,
                "password": "pw",
            },
        )

        assert resp.status == HTTPStatus.UNAUTHORIZED


class TestGetRole:
    """Test get_role: action construction and response mapping."""

    @pytest.mark.asyncio
    async def test_round_trip_with_group(
        self,
        client: Any,
        mock_processors: MagicMock,
        user_uuid: uuid.UUID,
    ) -> None:
        """Request with group_id maps to action and result maps to response."""
        group_id = uuid.uuid4()
        action_result = GetRoleActionResult(
            global_role="user",
            domain_role="admin",
            group_role="member",
        )
        mock_processors.auth.get_role.wait_for_complete = AsyncMock(return_value=action_result)

        resp = await client.get("/auth/role", params={"group": str(group_id)})

        action = mock_processors.auth.get_role.wait_for_complete.call_args[0][0]
        assert action.user_id == user_uuid
        assert action.group_id == group_id

        assert resp.status == HTTPStatus.OK
        data = await resp.json()
        assert data["global_role"] == "user"
        assert data["domain_role"] == "admin"
        assert data["group_role"] == "member"


class TestSignup:
    """Test signup handler: action construction from optional fields and response mapping."""

    @pytest.mark.asyncio
    async def test_full_fields_round_trip(
        self,
        client: Any,
        mock_processors: MagicMock,
    ) -> None:
        """All fields provided: request → action mapping, ActionResult → response."""
        signup_domain = "custom-domain"
        signup_email = "new@test.com"
        signup_password = "pw"
        signup_username = "newuser"
        signup_full_name = "New User"
        signup_description = "desc"
        result_access_key = "AK_SIGNUP"
        result_secret_key = "SK_SIGNUP"

        action_result = SignupActionResult(
            user_id=uuid.uuid4(),
            access_key=result_access_key,
            secret_key=result_secret_key,
        )
        mock_processors.auth.signup.wait_for_complete = AsyncMock(return_value=action_result)

        resp = await client.post(
            "/auth/signup",
            json={
                "domain": signup_domain,
                "email": signup_email,
                "password": signup_password,
                "username": signup_username,
                "full_name": signup_full_name,
                "description": signup_description,
            },
        )

        action = mock_processors.auth.signup.wait_for_complete.call_args[0][0]
        assert action.domain_name == signup_domain
        assert action.email == signup_email
        assert action.password == signup_password
        assert action.username == signup_username
        assert action.full_name == signup_full_name
        assert action.description == signup_description

        assert resp.status == HTTPStatus.CREATED
        data = await resp.json()
        assert data["access_key"] == result_access_key
        assert data["secret_key"] == result_secret_key

    @pytest.mark.asyncio
    async def test_optional_fields_default_to_none(
        self,
        client: Any,
        mock_processors: MagicMock,
    ) -> None:
        """When optional fields (username, full_name, description) are omitted, action gets None."""
        action_result = SignupActionResult(
            user_id=uuid.uuid4(),
            access_key="AK",
            secret_key="SK",
        )
        mock_processors.auth.signup.wait_for_complete = AsyncMock(return_value=action_result)

        resp = await client.post(
            "/auth/signup",
            json={
                "domain": USER_DOMAIN,
                "email": "minimal@test.com",
                "password": "pw",
            },
        )

        action = mock_processors.auth.signup.wait_for_complete.call_args[0][0]
        assert action.username is None
        assert action.full_name is None
        assert action.description is None
        assert resp.status == HTTPStatus.CREATED


class TestSignout:
    """Test signout maps user_ctx fields (not request body) to action identity fields."""

    @pytest.mark.asyncio
    async def test_identity_from_user_ctx(
        self,
        client: Any,
        mock_processors: MagicMock,
        user_uuid: uuid.UUID,
    ) -> None:
        """user_id and requester_email come from authenticated context, not body."""
        target_email = "target@test.com"
        target_password = "pw"
        mock_processors.auth.signout.wait_for_complete = AsyncMock(
            return_value=SignoutActionResult(success=True)
        )

        resp = await client.post(
            "/auth/signout",
            json={"email": target_email, "password": target_password},
        )

        action = mock_processors.auth.signout.wait_for_complete.call_args[0][0]
        assert action.user_id == user_uuid
        assert action.requester_email == USER_EMAIL
        assert action.domain_name == USER_DOMAIN
        assert action.email == target_email
        assert action.password == target_password
        assert resp.status == HTTPStatus.OK


class TestUpdatePassword:
    """Test update_password: action construction, success/failure response branching."""

    @pytest.mark.asyncio
    async def test_success_round_trip(
        self,
        client: Any,
        mock_processors: MagicMock,
        user_uuid: uuid.UUID,
    ) -> None:
        """On success: verify action fields from body+user_ctx, response has no error."""
        old_pw = "old-pw"
        new_pw = "new-pw"
        mock_processors.auth.update_password.wait_for_complete = AsyncMock(
            return_value=UpdatePasswordActionResult(success=True, message="OK")
        )

        resp = await client.post(
            "/auth/password",
            json={
                "old_password": old_pw,
                "new_password": new_pw,
                "new_password2": new_pw,
            },
        )

        action = mock_processors.auth.update_password.wait_for_complete.call_args[0][0]
        assert action.user_id == user_uuid
        assert action.email == USER_EMAIL
        assert action.domain_name == USER_DOMAIN
        assert action.old_password == old_pw
        assert action.new_password == new_pw
        assert action.new_password_confirm == new_pw

        assert resp.status == HTTPStatus.OK
        data = await resp.json()
        assert data.get("error_msg") is None

    @pytest.mark.asyncio
    async def test_failure_returns_bad_request(
        self,
        client: Any,
        mock_processors: MagicMock,
    ) -> None:
        """On failure: handler returns 400 with hardcoded error message (not from result)."""
        mock_processors.auth.update_password.wait_for_complete = AsyncMock(
            return_value=UpdatePasswordActionResult(success=False, message="ignored-by-handler")
        )

        resp = await client.post(
            "/auth/password",
            json={
                "old_password": "old",
                "new_password": "new1",
                "new_password2": "new2",
            },
        )

        assert resp.status == HTTPStatus.BAD_REQUEST
        data = await resp.json()
        assert data["error_msg"] == "new password mismatch"


class TestUpdatePasswordNoAuth:
    """Test update_password_no_auth: no auth required, action/response mapping."""

    @pytest.mark.asyncio
    async def test_round_trip(
        self,
        client: Any,
        mock_processors: MagicMock,
    ) -> None:
        """Request fields map to action, result.password_changed_at maps to response."""
        request_domain = "my-domain"
        request_email = "expired@test.com"
        current_pw = "current-pw"
        new_pw = "new-pw"
        changed_at = datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC)

        mock_processors.auth.update_password_no_auth.wait_for_complete = AsyncMock(
            return_value=UpdatePasswordNoAuthActionResult(
                user_id=uuid.uuid4(),
                password_changed_at=changed_at,
            )
        )

        resp = await client.post(
            "/auth/password-no-auth",
            json={
                "domain": request_domain,
                "username": request_email,
                "current_password": current_pw,
                "new_password": new_pw,
            },
        )

        action = mock_processors.auth.update_password_no_auth.wait_for_complete.call_args[0][0]
        assert action.domain_name == request_domain
        assert action.email == request_email
        assert action.current_password == current_pw
        assert action.new_password == new_pw

        assert resp.status == HTTPStatus.CREATED
        data = await resp.json()
        assert data["password_changed_at"] == changed_at.isoformat()


class TestUpdateFullName:
    """Test update_full_name: identity comes from user_ctx, not from request body."""

    @pytest.mark.asyncio
    async def test_identity_from_user_ctx_not_body(
        self,
        client: Any,
        mock_processors: MagicMock,
        user_uuid: uuid.UUID,
    ) -> None:
        """Action identity fields come from user_ctx even if body supplies different email."""
        attacker_email = "attacker@evil.com"
        new_name = "New Name"
        mock_processors.auth.update_full_name.wait_for_complete = AsyncMock(
            return_value=UpdateFullNameActionResult(success=True)
        )

        resp = await client.post(
            "/auth/full-name",
            json={"email": attacker_email, "full_name": new_name},
        )

        action = mock_processors.auth.update_full_name.wait_for_complete.call_args[0][0]
        assert action.email == USER_EMAIL
        assert action.email != attacker_email
        assert action.domain_name == USER_DOMAIN
        assert action.user_id == str(user_uuid)
        assert action.full_name == new_name
        assert resp.status == HTTPStatus.OK


class TestGetSSHKeypair:
    """Test get_ssh_keypair: action uses user_ctx, response maps from result."""

    @pytest.mark.asyncio
    async def test_round_trip(
        self,
        client: Any,
        mock_processors: MagicMock,
        user_uuid: uuid.UUID,
    ) -> None:
        """Public key from result maps to response; action uses user_ctx identity."""
        stored_pubkey = "ssh-rsa AAAA...stored\n"
        mock_processors.auth.get_ssh_keypair.wait_for_complete = AsyncMock(
            return_value=GetSSHKeypairActionResult(public_key=stored_pubkey)
        )

        resp = await client.get("/auth/ssh-keypair")

        action = mock_processors.auth.get_ssh_keypair.wait_for_complete.call_args[0][0]
        assert action.user_id == user_uuid
        assert action.access_key == ACCESS_KEY

        assert resp.status == HTTPStatus.OK
        data = await resp.json()
        assert data["ssh_public_key"] == stored_pubkey


class TestGenerateSSHKeypair:
    """Test generate_ssh_keypair: action uses user_ctx, response maps both keys."""

    @pytest.mark.asyncio
    async def test_round_trip(
        self,
        client: Any,
        mock_processors: MagicMock,
        user_uuid: uuid.UUID,
    ) -> None:
        """Generated keypair from result maps to response."""
        generated_pub = "ssh-rsa GENERATED_PUB\n"
        generated_priv = "-----BEGIN RSA PRIVATE KEY-----\nGENERATED\n"
        mock_processors.auth.generate_ssh_keypair.wait_for_complete = AsyncMock(
            return_value=GenerateSSHKeypairActionResult(
                ssh_keypair=SSHKeypair(
                    ssh_public_key=generated_pub,
                    ssh_private_key=generated_priv,
                )
            )
        )

        resp = await client.patch("/auth/ssh-keypair")

        action = mock_processors.auth.generate_ssh_keypair.wait_for_complete.call_args[0][0]
        assert action.user_id == user_uuid
        assert action.access_key == ACCESS_KEY

        assert resp.status == HTTPStatus.OK
        data = await resp.json()
        assert data["ssh_public_key"] == generated_pub
        assert data["ssh_private_key"] == generated_priv


class TestUploadSSHKeypair:
    """Test upload_ssh_keypair: trailing newline normalization and result→response mapping."""

    @pytest.mark.asyncio
    async def test_normalizes_trailing_newline(
        self,
        client: Any,
        mock_processors: MagicMock,
        user_uuid: uuid.UUID,
    ) -> None:
        """Keys without trailing newline get one appended; response maps from result."""
        input_pubkey = "ssh-rsa AAA..."
        input_privkey = "-----BEGIN RSA PRIVATE KEY-----\n..."
        stored_pubkey = "ssh-rsa STORED_PUB\n"
        stored_privkey = "-----BEGIN RSA PRIVATE KEY-----\nSTORED\n"

        result_keypair = SSHKeypair(
            ssh_public_key=stored_pubkey,
            ssh_private_key=stored_privkey,
        )
        mock_processors.auth.upload_ssh_keypair.wait_for_complete = AsyncMock(
            return_value=UploadSSHKeypairActionResult(ssh_keypair=result_keypair)
        )

        resp = await client.post(
            "/auth/ssh-keypair/upload",
            json={"pubkey": input_pubkey, "privkey": input_privkey},
        )

        action = mock_processors.auth.upload_ssh_keypair.wait_for_complete.call_args[0][0]
        assert action.public_key == f"{input_pubkey}\n"
        assert action.private_key == f"{input_privkey}\n"
        assert action.user_id == user_uuid
        assert action.access_key == ACCESS_KEY

        assert resp.status == HTTPStatus.OK
        data = await resp.json()
        assert data["ssh_public_key"] == stored_pubkey
        assert data["ssh_private_key"] == stored_privkey
        assert data["ssh_public_key"] != action.public_key
