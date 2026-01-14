"""
Tests for auth API handler with HTTP mocking.
Tests @api_handler decorated endpoints using aiohttp_client.
"""

from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from aiohttp import web
from aiohttp.typedefs import Middleware

from ai.backend.manager.api.auth.handler import AuthAPIHandler
from ai.backend.manager.data.auth.types import SSHKeypair
from ai.backend.manager.dto.context import ProcessorsCtx, RequestCtx
from ai.backend.manager.services.auth.actions.generate_ssh_keypair import (
    GenerateSSHKeypairActionResult,
)
from ai.backend.manager.services.auth.actions.get_role import GetRoleActionResult
from ai.backend.manager.services.auth.actions.get_ssh_keypair import GetSSHKeypairActionResult
from ai.backend.manager.services.auth.actions.signup import SignupActionResult
from ai.backend.manager.services.auth.actions.update_full_name import UpdateFullNameActionResult
from ai.backend.manager.services.auth.actions.update_password import UpdatePasswordActionResult
from ai.backend.manager.services.auth.actions.update_password_no_auth import (
    UpdatePasswordNoAuthActionResult,
)
from ai.backend.manager.services.auth.actions.upload_ssh_keypair import UploadSSHKeypairActionResult

if TYPE_CHECKING:
    from aiohttp.test_utils import TestClient


@pytest.fixture
def handler() -> AuthAPIHandler:
    """Create AuthAPIHandler instance."""
    return AuthAPIHandler()


@pytest.fixture
def mock_processors() -> MagicMock:
    """Create mock processors with auth-related action processors."""
    processors = MagicMock()
    processors.auth = MagicMock()
    processors.auth.get_role = MagicMock()
    processors.auth.signup = MagicMock()
    processors.auth.update_password = MagicMock()
    processors.auth.update_password_no_auth = MagicMock()
    processors.auth.update_full_name = MagicMock()
    processors.auth.get_ssh_keypair = MagicMock()
    processors.auth.generate_ssh_keypair = MagicMock()
    processors.auth.upload_ssh_keypair = MagicMock()
    return processors


@pytest.fixture
def user_uuid() -> Any:
    """Create user UUID for tests."""
    return uuid4()


@pytest.fixture
def mock_user_data(user_uuid: Any) -> dict[str, Any]:
    """Create mock user data for authentication context."""
    return {
        "uuid": user_uuid,
        "email": "test@example.com",
        "domain_name": "default",
    }


@pytest.fixture
def mock_keypair_data() -> dict[str, Any]:
    """Create mock keypair data for authentication context."""
    return {"access_key": "TESTKEY123"}


@pytest.fixture
def auth_middleware(
    mock_user_data: dict[str, Any], mock_keypair_data: dict[str, Any]
) -> Middleware:
    """Create middleware that sets authentication context."""

    @web.middleware
    async def middleware(request: web.Request, handler: Any) -> web.StreamResponse:
        request["user"] = mock_user_data
        request["keypair"] = mock_keypair_data
        request["is_authorized"] = True
        request["is_admin"] = False
        request["is_superadmin"] = False
        return await handler(request)

    return middleware


@pytest.fixture
def app(
    handler: AuthAPIHandler,
    auth_middleware: Middleware,
) -> web.Application:
    """Create aiohttp app with auth handler routes."""
    app = web.Application(middlewares=[auth_middleware])

    app.router.add_get("/auth/test", handler.test)
    app.router.add_get("/auth/role", handler.get_role)
    app.router.add_post("/auth/signup", handler.signup)
    app.router.add_post("/auth/password", handler.update_password)
    app.router.add_post("/auth/password-no-auth", handler.update_password_no_auth)
    app.router.add_post("/auth/full-name", handler.update_full_name)
    app.router.add_get("/auth/ssh-keypair", handler.get_ssh_keypair)
    app.router.add_post("/auth/ssh-keypair/generate", handler.generate_ssh_keypair)
    app.router.add_post("/auth/ssh-keypair/upload", handler.upload_ssh_keypair)

    return app


@pytest.fixture
def patch_middleware_params(mock_processors: MagicMock) -> Any:
    """Patch MiddlewareParam.from_request methods to return mocks."""

    async def mock_processors_ctx_from_request(cls: Any, request: web.Request) -> MagicMock:
        ctx = MagicMock()
        ctx.processors = mock_processors
        return ctx

    async def mock_request_ctx_from_request(cls: Any, request: web.Request) -> MagicMock:
        ctx = MagicMock()
        ctx.request = request
        return ctx

    return patch.object(
        ProcessorsCtx,
        "from_request",
        classmethod(mock_processors_ctx_from_request),
    ), patch.object(
        RequestCtx,
        "from_request",
        classmethod(mock_request_ctx_from_request),
    )


class TestAuthHandlerTest:
    """Test cases for test endpoint."""

    @pytest.mark.asyncio
    async def test_auth_test_success(
        self,
        aiohttp_client: Any,
        app: web.Application,
    ) -> None:
        """Test test endpoint returns authorized status."""
        expected_authorized = "yes"

        client: TestClient = await aiohttp_client(app)
        resp = await client.get("/auth/test")

        assert resp.status == HTTPStatus.OK
        data = await resp.json()
        assert data["authorized"] == expected_authorized


class TestAuthHandlerGetRole:
    """Test cases for get_role endpoint."""

    @pytest.mark.asyncio
    async def test_get_role_success(
        self,
        aiohttp_client: Any,
        app: web.Application,
        mock_processors: MagicMock,
        patch_middleware_params: Any,
    ) -> None:
        """Test get_role returns user role information."""
        expected_global_role = "user"
        expected_domain_role = "admin"
        expected_group_role = "manager"

        mock_processors.auth.get_role.wait_for_complete = AsyncMock(
            return_value=GetRoleActionResult(
                global_role=expected_global_role,
                domain_role=expected_domain_role,
                group_role=expected_group_role,
            )
        )

        processors_ctx_patch, request_ctx_patch = patch_middleware_params
        with processors_ctx_patch, request_ctx_patch:
            client: TestClient = await aiohttp_client(app)
            resp = await client.get("/auth/role")

        assert resp.status == HTTPStatus.OK
        data = await resp.json()
        assert data["global_role"] == expected_global_role
        assert data["domain_role"] == expected_domain_role
        assert data["group_role"] == expected_group_role


class TestAuthHandlerSignup:
    """Test cases for signup endpoint."""

    @pytest.mark.asyncio
    async def test_signup_success(
        self,
        aiohttp_client: Any,
        app: web.Application,
        mock_processors: MagicMock,
        patch_middleware_params: Any,
    ) -> None:
        """Test signup creates new user and returns credentials."""
        expected_access_key = "NEWKEY123"
        expected_secret_key = "NEWSECRET456"

        mock_processors.auth.signup.wait_for_complete = AsyncMock(
            return_value=SignupActionResult(
                user_id=uuid4(),
                access_key=expected_access_key,
                secret_key=expected_secret_key,
            )
        )

        processors_ctx_patch, request_ctx_patch = patch_middleware_params
        with processors_ctx_patch, request_ctx_patch:
            client: TestClient = await aiohttp_client(app)
            resp = await client.post(
                "/auth/signup",
                json={
                    "domain": "default",
                    "email": "newuser@example.com",
                    "password": "securepass123",
                },
            )

        assert resp.status == HTTPStatus.CREATED
        data = await resp.json()
        assert data["access_key"] == expected_access_key
        assert data["secret_key"] == expected_secret_key


class TestAuthHandlerUpdatePassword:
    """Test cases for update_password endpoint."""

    @pytest.mark.asyncio
    async def test_update_password_success(
        self,
        aiohttp_client: Any,
        app: web.Application,
        mock_processors: MagicMock,
        patch_middleware_params: Any,
    ) -> None:
        """Test update_password updates password successfully."""
        mock_processors.auth.update_password.wait_for_complete = AsyncMock(
            return_value=UpdatePasswordActionResult(success=True, message="")
        )

        processors_ctx_patch, request_ctx_patch = patch_middleware_params
        with processors_ctx_patch, request_ctx_patch:
            client: TestClient = await aiohttp_client(app)
            resp = await client.post(
                "/auth/password",
                json={
                    "old_password": "oldpass123",
                    "new_password": "newpass456",
                    "new_password2": "newpass456",
                },
            )

        assert resp.status == HTTPStatus.OK
        data = await resp.json()
        assert data.get("error_msg") is None

    @pytest.mark.asyncio
    async def test_update_password_mismatch(
        self,
        aiohttp_client: Any,
        app: web.Application,
        mock_processors: MagicMock,
        patch_middleware_params: Any,
    ) -> None:
        """Test update_password returns error on password mismatch."""
        expected_error_msg = "new password mismatch"

        mock_processors.auth.update_password.wait_for_complete = AsyncMock(
            return_value=UpdatePasswordActionResult(success=False, message="new password mismatch")
        )

        processors_ctx_patch, request_ctx_patch = patch_middleware_params
        with processors_ctx_patch, request_ctx_patch:
            client: TestClient = await aiohttp_client(app)
            resp = await client.post(
                "/auth/password",
                json={
                    "old_password": "oldpass123",
                    "new_password": "newpass456",
                    "new_password2": "wrongpass789",
                },
            )

        assert resp.status == HTTPStatus.BAD_REQUEST
        data = await resp.json()
        assert data["error_msg"] == expected_error_msg


class TestAuthHandlerUpdatePasswordNoAuth:
    """Test cases for update_password_no_auth endpoint."""

    @pytest.mark.asyncio
    async def test_update_password_no_auth_success(
        self,
        aiohttp_client: Any,
        app: web.Application,
        mock_processors: MagicMock,
        patch_middleware_params: Any,
    ) -> None:
        """Test update_password_no_auth updates expired password."""
        expected_password_changed_at = datetime.now(tz=UTC)

        mock_processors.auth.update_password_no_auth.wait_for_complete = AsyncMock(
            return_value=UpdatePasswordNoAuthActionResult(
                user_id=uuid4(),
                password_changed_at=expected_password_changed_at,
            )
        )

        processors_ctx_patch, request_ctx_patch = patch_middleware_params
        with processors_ctx_patch, request_ctx_patch:
            client: TestClient = await aiohttp_client(app)
            resp = await client.post(
                "/auth/password-no-auth",
                json={
                    "domain": "default",
                    "username": "user@example.com",
                    "current_password": "currentpass",
                    "new_password": "newpass456",
                },
            )

        assert resp.status == HTTPStatus.CREATED
        data = await resp.json()
        assert "password_changed_at" in data


class TestAuthHandlerUpdateFullName:
    """Test cases for update_full_name endpoint."""

    @pytest.mark.asyncio
    async def test_update_full_name_success(
        self,
        aiohttp_client: Any,
        app: web.Application,
        mock_processors: MagicMock,
        patch_middleware_params: Any,
    ) -> None:
        """Test update_full_name updates user's full name."""
        mock_processors.auth.update_full_name.wait_for_complete = AsyncMock(
            return_value=UpdateFullNameActionResult(success=True)
        )

        processors_ctx_patch, request_ctx_patch = patch_middleware_params
        with processors_ctx_patch, request_ctx_patch:
            client: TestClient = await aiohttp_client(app)
            resp = await client.post(
                "/auth/full-name",
                json={
                    "email": "user@example.com",
                    "full_name": "Updated Name",
                },
            )

        assert resp.status == HTTPStatus.OK


class TestAuthHandlerSSHKeypair:
    """Test cases for SSH keypair endpoints."""

    @pytest.mark.asyncio
    async def test_get_ssh_keypair_success(
        self,
        aiohttp_client: Any,
        app: web.Application,
        mock_processors: MagicMock,
        patch_middleware_params: Any,
    ) -> None:
        """Test get_ssh_keypair returns public key."""
        expected_public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... user@host\n"

        mock_processors.auth.get_ssh_keypair.wait_for_complete = AsyncMock(
            return_value=GetSSHKeypairActionResult(public_key=expected_public_key)
        )

        processors_ctx_patch, request_ctx_patch = patch_middleware_params
        with processors_ctx_patch, request_ctx_patch:
            client: TestClient = await aiohttp_client(app)
            resp = await client.get("/auth/ssh-keypair")

        assert resp.status == HTTPStatus.OK
        data = await resp.json()
        assert data["ssh_public_key"] == expected_public_key

    @pytest.mark.asyncio
    async def test_generate_ssh_keypair_success(
        self,
        aiohttp_client: Any,
        app: web.Application,
        mock_processors: MagicMock,
        patch_middleware_params: Any,
    ) -> None:
        """Test generate_ssh_keypair creates new keypair."""
        expected_public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... user@host\n"
        expected_private_key = (
            "-----BEGIN RSA PRIVATE KEY-----\nMIIG4...\n-----END RSA PRIVATE KEY-----\n"
        )

        mock_processors.auth.generate_ssh_keypair.wait_for_complete = AsyncMock(
            return_value=GenerateSSHKeypairActionResult(
                ssh_keypair=SSHKeypair(
                    ssh_public_key=expected_public_key,
                    ssh_private_key=expected_private_key,
                )
            )
        )

        processors_ctx_patch, request_ctx_patch = patch_middleware_params
        with processors_ctx_patch, request_ctx_patch:
            client: TestClient = await aiohttp_client(app)
            resp = await client.post("/auth/ssh-keypair/generate")

        assert resp.status == HTTPStatus.OK
        data = await resp.json()
        assert data["ssh_public_key"] == expected_public_key
        assert data["ssh_private_key"] == expected_private_key

    @pytest.mark.asyncio
    async def test_upload_ssh_keypair_success(
        self,
        aiohttp_client: Any,
        app: web.Application,
        mock_processors: MagicMock,
        patch_middleware_params: Any,
    ) -> None:
        """Test upload_ssh_keypair stores custom keypair."""
        input_public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... user@host"
        input_private_key = (
            "-----BEGIN RSA PRIVATE KEY-----\nMIIG4...\n-----END RSA PRIVATE KEY-----"
        )
        expected_public_key = f"{input_public_key}\n"
        expected_private_key = f"{input_private_key}\n"

        mock_processors.auth.upload_ssh_keypair.wait_for_complete = AsyncMock(
            return_value=UploadSSHKeypairActionResult(
                ssh_keypair=SSHKeypair(
                    ssh_public_key=expected_public_key,
                    ssh_private_key=expected_private_key,
                )
            )
        )

        processors_ctx_patch, request_ctx_patch = patch_middleware_params
        with processors_ctx_patch, request_ctx_patch:
            client: TestClient = await aiohttp_client(app)
            resp = await client.post(
                "/auth/ssh-keypair/upload",
                json={
                    "pubkey": input_public_key,
                    "privkey": input_private_key,
                },
            )

        assert resp.status == HTTPStatus.OK
        data = await resp.json()
        assert data["ssh_public_key"] == expected_public_key
        assert data["ssh_private_key"] == expected_private_key
