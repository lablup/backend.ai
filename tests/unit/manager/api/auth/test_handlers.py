"""
Tests for auth.py API handlers.

TODO: Currently auth decorators (auth_required) are bypassed
      by mocking request.get(). This should be refactored to use proper middleware
      integration for more realistic testing.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest
from aiohttp import web

from ai.backend.manager.api.auth import (
    authorize,
    generate_ssh_keypair,
    get_role,
    get_ssh_keypair,
    signout,
    signup,
    update_full_name,
    update_password,
    update_password_no_auth,
    upload_ssh_keypair,
)
from ai.backend.manager.data.auth.types import AuthorizationResult, SSHKeypair
from ai.backend.manager.errors.auth import AuthorizationFailed
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
def mock_root_ctx() -> MagicMock:
    """RootContext mock with processors."""
    return MagicMock()


@pytest.fixture
def unauthorized_request(mock_root_ctx: MagicMock) -> MagicMock:
    """Mock request for unauthorized user."""
    req = MagicMock(spec=web.Request)
    req.app = {"_root.context": mock_root_ctx}
    req.get = lambda k, default=None: {
        "is_authorized": False,
        "is_superadmin": False,
    }.get(k, default)
    return req


@pytest.fixture
def authorized_request(mock_root_ctx: MagicMock) -> MagicMock:
    """Mock request for authorized user with POST body support."""
    req = MagicMock(spec=web.Request)
    req.app = {"_root.context": mock_root_ctx}
    req.get = lambda k, default=None: {
        "is_authorized": True,
        "is_superadmin": False,
        "is_admin": False,
    }.get(k, default)
    type(req).can_read_body = PropertyMock(return_value=True)
    req.method = "POST"
    req.content_type = "application/json"
    storage: dict[str, Any] = {}
    req.__getitem__ = lambda _, key: storage[key]
    req.__setitem__ = lambda _, key, value: storage.__setitem__(key, value)
    return req


@pytest.fixture
def public_request(mock_root_ctx: MagicMock) -> MagicMock:
    """Mock request for public endpoints (no auth required)."""
    req = MagicMock(spec=web.Request)
    req.app = {"_root.context": mock_root_ctx}
    type(req).can_read_body = PropertyMock(return_value=True)
    req.method = "POST"
    req.content_type = "application/json"
    return req


# ---------------------------------------------------------------------------
# Test Classes
# ---------------------------------------------------------------------------


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
        public_request: MagicMock,
        mock_root_ctx: MagicMock,
        authorize_result: AuthorizeActionResult,
    ) -> None:
        """Verify processor is called and authorization result is returned."""
        public_request.text = AsyncMock(
            return_value=json.dumps({
                "type": "keypair",
                "domain": "default",
                "username": "test@example.com",
                "password": "password123",
            })
        )
        mock_root_ctx.processors.auth.authorize.wait_for_complete = AsyncMock(
            return_value=authorize_result
        )

        response = await authorize(public_request)

        mock_root_ctx.processors.auth.authorize.wait_for_complete.assert_called_once()
        assert response.status == HTTPStatus.OK
        # keypair type returns web.Response (not StreamResponse)
        json_response = cast(web.Response, response)
        response_body = json.loads(cast(bytes, json_response.body))
        assert authorize_result.authorization_result is not None
        assert (
            response_body["data"]["access_key"] == authorize_result.authorization_result.access_key
        )
        assert (
            response_body["data"]["secret_key"] == authorize_result.authorization_result.secret_key
        )

    @pytest.mark.asyncio
    async def test_passes_params_to_action(
        self,
        public_request: MagicMock,
        mock_root_ctx: MagicMock,
        authorize_result: AuthorizeActionResult,
    ) -> None:
        """Verify domain, username, password are passed to Action."""
        domain = "test-domain"
        email = "user@example.com"
        password = "jwtpass"
        stoken = "session-token"
        public_request.text = AsyncMock(
            return_value=json.dumps({
                "type": "jwt",
                "domain": domain,
                "username": email,
                "password": password,
                "stoken": stoken,
            })
        )
        mock_root_ctx.processors.auth.authorize.wait_for_complete = AsyncMock(
            return_value=authorize_result
        )

        await authorize(public_request)

        action = mock_root_ctx.processors.auth.authorize.wait_for_complete.call_args[0][0]
        assert action.domain_name == domain
        assert action.email == email
        assert action.password == password
        assert action.stoken == stoken


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
        public_request: MagicMock,
        mock_root_ctx: MagicMock,
        signup_result: SignupActionResult,
    ) -> None:
        """Verify processor is called and HTTP 201 CREATED is returned."""
        public_request.text = AsyncMock(
            return_value=json.dumps({
                "domain": "default",
                "email": "newuser@example.com",
                "password": "securepassword",
            })
        )
        mock_root_ctx.processors.auth.signup.wait_for_complete = AsyncMock(
            return_value=signup_result
        )

        response = await signup(public_request)

        mock_root_ctx.processors.auth.signup.wait_for_complete.assert_called_once()
        assert response.status == HTTPStatus.CREATED
        response_body = json.loads(cast(bytes, response.body))
        assert response_body["access_key"] == signup_result.access_key
        assert response_body["secret_key"] == signup_result.secret_key

    @pytest.mark.asyncio
    async def test_passes_optional_params_to_action(
        self,
        public_request: MagicMock,
        mock_root_ctx: MagicMock,
        signup_result: SignupActionResult,
    ) -> None:
        """Verify optional params are passed to Action."""
        domain = "custom-domain"
        email = "fulluser@example.com"
        username = "fulluser"
        full_name = "Full Name"
        public_request.text = AsyncMock(
            return_value=json.dumps({
                "domain": domain,
                "email": email,
                "password": "password",
                "username": username,
                "full_name": full_name,
                "description": "Description",
            })
        )
        mock_root_ctx.processors.auth.signup.wait_for_complete = AsyncMock(
            return_value=signup_result
        )

        await signup(public_request)

        action = mock_root_ctx.processors.auth.signup.wait_for_complete.call_args[0][0]
        assert action.domain_name == domain
        assert action.email == email
        assert action.username == username
        assert action.full_name == full_name


class TestSignout:
    """Tests for signout handler."""

    @pytest.mark.asyncio
    async def test_calls_processor(
        self,
        authorized_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify processor is called and empty response is returned."""
        user_uuid = uuid.uuid4()
        email = "test@example.com"
        authorized_request.text = AsyncMock(
            return_value=json.dumps({"email": email, "password": "pass"})
        )
        authorized_request["user"] = {
            "uuid": user_uuid,
            "email": email,
            "domain_name": "default",
        }
        authorized_request["keypair"] = {"access_key": "AKTEST"}
        mock_root_ctx.processors.auth.signout.wait_for_complete = AsyncMock(
            return_value=SignoutActionResult(success=True)
        )

        response = await signout(authorized_request)

        mock_root_ctx.processors.auth.signout.wait_for_complete.assert_called_once()
        action = mock_root_ctx.processors.auth.signout.wait_for_complete.call_args[0][0]
        assert action.user_id == user_uuid
        assert action.email == email
        assert response.status == HTTPStatus.OK

    @pytest.mark.asyncio
    async def test_rejects_unauthorized_request(
        self,
        unauthorized_request: MagicMock,
    ) -> None:
        """Verify unauthorized request is rejected."""
        with pytest.raises(AuthorizationFailed):
            await signout(unauthorized_request)


class TestGetRole:
    """Tests for get_role handler."""

    @pytest.mark.asyncio
    async def test_calls_processor_and_returns_roles(
        self,
        authorized_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify processor is called and roles are returned."""
        user_uuid = uuid.uuid4()
        global_role = "user"
        domain_role = "user"
        # Configure for GET request
        type(authorized_request).can_read_body = PropertyMock(return_value=False)
        authorized_request.method = "GET"
        authorized_request.query = {}
        authorized_request["user"] = {"uuid": user_uuid, "domain_name": "default"}
        authorized_request["keypair"] = {"access_key": "AKTEST"}
        authorized_request["is_superadmin"] = False
        authorized_request["is_admin"] = False
        mock_root_ctx.processors.auth.get_role.wait_for_complete = AsyncMock(
            return_value=GetRoleActionResult(
                global_role=global_role,
                domain_role=domain_role,
                group_role=None,
            )
        )

        response = await get_role(authorized_request)

        mock_root_ctx.processors.auth.get_role.wait_for_complete.assert_called_once()
        assert response.status == HTTPStatus.OK
        response_body = json.loads(cast(bytes, response.body))
        assert response_body["global_role"] == global_role
        assert response_body["domain_role"] == domain_role
        assert response_body["group_role"] is None

    @pytest.mark.asyncio
    async def test_passes_group_to_action(
        self,
        authorized_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify group parameter is passed to Action."""
        user_uuid = uuid.uuid4()
        group_uuid = uuid.uuid4()
        type(authorized_request).can_read_body = PropertyMock(return_value=False)
        authorized_request.method = "GET"
        authorized_request.query = {"group": str(group_uuid)}
        authorized_request["user"] = {"uuid": user_uuid, "domain_name": "default"}
        authorized_request["keypair"] = {"access_key": "AKTEST"}
        authorized_request["is_superadmin"] = False
        authorized_request["is_admin"] = False
        mock_root_ctx.processors.auth.get_role.wait_for_complete = AsyncMock(
            return_value=GetRoleActionResult(
                global_role="user",
                domain_role="user",
                group_role="member",
            )
        )

        await get_role(authorized_request)

        action = mock_root_ctx.processors.auth.get_role.wait_for_complete.call_args[0][0]
        assert action.group_id == group_uuid

    @pytest.mark.asyncio
    async def test_rejects_unauthorized_request(
        self,
        unauthorized_request: MagicMock,
    ) -> None:
        """Verify unauthorized request is rejected."""
        with pytest.raises(AuthorizationFailed):
            await get_role(unauthorized_request)


class TestUpdatePassword:
    """Tests for update_password handler."""

    @pytest.mark.asyncio
    async def test_calls_processor_on_success(
        self,
        authorized_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify processor is called and OK is returned on success."""
        user_uuid = uuid.uuid4()
        authorized_request.text = AsyncMock(
            return_value=json.dumps({
                "old_password": "oldpass",
                "new_password": "newpass",
                "new_password2": "newpass",
            })
        )
        authorized_request["user"] = {
            "uuid": user_uuid,
            "email": "test@example.com",
            "domain_name": "default",
        }
        authorized_request["keypair"] = {"access_key": "AKTEST"}
        mock_root_ctx.processors.auth.update_password.wait_for_complete = AsyncMock(
            return_value=UpdatePasswordActionResult(success=True, message="OK")
        )

        response = await update_password(authorized_request)

        mock_root_ctx.processors.auth.update_password.wait_for_complete.assert_called_once()
        assert response.status == HTTPStatus.OK

    @pytest.mark.asyncio
    async def test_returns_bad_request_on_failure(
        self,
        authorized_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify BAD_REQUEST is returned when password update fails."""
        user_uuid = uuid.uuid4()
        authorized_request.text = AsyncMock(
            return_value=json.dumps({
                "old_password": "oldpass",
                "new_password": "newpass",
                "new_password2": "differentpass",
            })
        )
        authorized_request["user"] = {
            "uuid": user_uuid,
            "email": "test@example.com",
            "domain_name": "default",
        }
        authorized_request["keypair"] = {"access_key": "AKTEST"}
        mock_root_ctx.processors.auth.update_password.wait_for_complete = AsyncMock(
            return_value=UpdatePasswordActionResult(success=False, message="mismatch")
        )

        response = await update_password(authorized_request)

        assert response.status == HTTPStatus.BAD_REQUEST

    @pytest.mark.asyncio
    async def test_rejects_unauthorized_request(
        self,
        unauthorized_request: MagicMock,
    ) -> None:
        """Verify unauthorized request is rejected."""
        with pytest.raises(AuthorizationFailed):
            await update_password(unauthorized_request)


class TestUpdatePasswordNoAuth:
    """Tests for update_password_no_auth handler (public endpoint)."""

    @pytest.mark.asyncio
    async def test_calls_processor_and_returns_created(
        self,
        public_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify processor is called and HTTP 201 CREATED is returned."""
        password_changed_at = datetime.now(tz=UTC)
        public_request.text = AsyncMock(
            return_value=json.dumps({
                "domain": "default",
                "username": "user@example.com",
                "current_password": "current",
                "new_password": "newpass",
            })
        )
        mock_root_ctx.processors.auth.update_password_no_auth.wait_for_complete = AsyncMock(
            return_value=UpdatePasswordNoAuthActionResult(
                user_id=uuid.uuid4(),
                password_changed_at=password_changed_at,
            )
        )

        response = await update_password_no_auth(public_request)

        mock_root_ctx.processors.auth.update_password_no_auth.wait_for_complete.assert_called_once()
        assert response.status == HTTPStatus.CREATED
        response_body = json.loads(cast(bytes, response.body))
        assert "password_changed_at" in response_body


class TestUpdateFullName:
    """Tests for update_full_name handler."""

    @pytest.mark.asyncio
    async def test_calls_processor(
        self,
        authorized_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify processor is called with correct params."""
        user_uuid = uuid.uuid4()
        email = "user@example.com"
        full_name = "New Name"
        authorized_request.text = AsyncMock(
            return_value=json.dumps({"email": email, "full_name": full_name})
        )
        authorized_request["user"] = {
            "uuid": user_uuid,
            "email": email,
            "domain_name": "default",
        }
        authorized_request["keypair"] = {"access_key": "AKTEST"}
        mock_root_ctx.processors.auth.update_full_name.wait_for_complete = AsyncMock(
            return_value=UpdateFullNameActionResult(success=True)
        )

        response = await update_full_name(authorized_request)

        mock_root_ctx.processors.auth.update_full_name.wait_for_complete.assert_called_once()
        action = mock_root_ctx.processors.auth.update_full_name.wait_for_complete.call_args[0][0]
        assert action.full_name == full_name
        assert response.status == HTTPStatus.OK

    @pytest.mark.asyncio
    async def test_rejects_unauthorized_request(
        self,
        unauthorized_request: MagicMock,
    ) -> None:
        """Verify unauthorized request is rejected."""
        with pytest.raises(AuthorizationFailed):
            await update_full_name(unauthorized_request)


class TestGetSSHKeypair:
    """Tests for get_ssh_keypair handler."""

    @pytest.mark.asyncio
    async def test_calls_processor_and_returns_public_key(
        self,
        authorized_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify processor is called and public key is returned."""
        user_uuid = uuid.uuid4()
        public_key = "ssh-rsa AAAAB3...\n"
        authorized_request["user"] = {"uuid": user_uuid, "domain_name": "default"}
        authorized_request["keypair"] = {"access_key": "AKTEST"}
        mock_root_ctx.processors.auth.get_ssh_keypair.wait_for_complete = AsyncMock(
            return_value=GetSSHKeypairActionResult(public_key=public_key)
        )

        response = await get_ssh_keypair(authorized_request)

        mock_root_ctx.processors.auth.get_ssh_keypair.wait_for_complete.assert_called_once()
        assert response.status == HTTPStatus.OK
        response_body = json.loads(cast(bytes, response.body))
        assert response_body["ssh_public_key"] == public_key

    @pytest.mark.asyncio
    async def test_rejects_unauthorized_request(
        self,
        unauthorized_request: MagicMock,
    ) -> None:
        """Verify unauthorized request is rejected."""
        with pytest.raises(AuthorizationFailed):
            await get_ssh_keypair(unauthorized_request)


class TestGenerateSSHKeypair:
    """Tests for generate_ssh_keypair handler."""

    @pytest.mark.asyncio
    async def test_calls_processor_and_returns_keypair(
        self,
        authorized_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify processor is called and keypair is returned."""
        user_uuid = uuid.uuid4()
        ssh_public_key = "ssh-rsa NEWPUB...\n"
        ssh_private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n"
        authorized_request["user"] = {"uuid": user_uuid, "domain_name": "default"}
        authorized_request["keypair"] = {"access_key": "AKTEST"}
        mock_root_ctx.processors.auth.generate_ssh_keypair.wait_for_complete = AsyncMock(
            return_value=GenerateSSHKeypairActionResult(
                ssh_keypair=SSHKeypair(
                    ssh_public_key=ssh_public_key,
                    ssh_private_key=ssh_private_key,
                )
            )
        )

        response = await generate_ssh_keypair(authorized_request)

        mock_root_ctx.processors.auth.generate_ssh_keypair.wait_for_complete.assert_called_once()
        assert response.status == HTTPStatus.OK
        response_body = json.loads(cast(bytes, response.body))
        assert response_body["ssh_public_key"] == ssh_public_key
        assert response_body["ssh_private_key"] == ssh_private_key

    @pytest.mark.asyncio
    async def test_rejects_unauthorized_request(
        self,
        unauthorized_request: MagicMock,
    ) -> None:
        """Verify unauthorized request is rejected."""
        with pytest.raises(AuthorizationFailed):
            await generate_ssh_keypair(unauthorized_request)


class TestUploadSSHKeypair:
    """Tests for upload_ssh_keypair handler."""

    @pytest.mark.asyncio
    async def test_calls_processor_and_returns_keypair(
        self,
        authorized_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify processor is called and keypair is returned."""
        user_uuid = uuid.uuid4()
        authorized_request.text = AsyncMock(
            return_value=json.dumps({
                "pubkey": "ssh-rsa AAAAB3...",
                "privkey": "-----BEGIN RSA PRIVATE KEY-----\n...",
            })
        )
        authorized_request["user"] = {"uuid": user_uuid, "domain_name": "default"}
        authorized_request["keypair"] = {"access_key": "AKTEST"}
        mock_root_ctx.processors.auth.upload_ssh_keypair.wait_for_complete = AsyncMock(
            return_value=UploadSSHKeypairActionResult(
                ssh_keypair=SSHKeypair(
                    ssh_public_key="ssh-rsa AAAAB3...\n",
                    ssh_private_key="-----BEGIN RSA PRIVATE KEY-----\n...\n",
                )
            )
        )

        response = await upload_ssh_keypair(authorized_request)

        mock_root_ctx.processors.auth.upload_ssh_keypair.wait_for_complete.assert_called_once()
        assert response.status == HTTPStatus.OK
        response_body = json.loads(cast(bytes, response.body))
        assert "ssh_public_key" in response_body
        assert "ssh_private_key" in response_body

    @pytest.mark.asyncio
    async def test_rejects_unauthorized_request(
        self,
        unauthorized_request: MagicMock,
    ) -> None:
        """Verify unauthorized request is rejected."""
        with pytest.raises(AuthorizationFailed):
            await upload_ssh_keypair(unauthorized_request)
