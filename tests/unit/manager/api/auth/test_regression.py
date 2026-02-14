"""
Regression tests for auth API handlers.
Compares old function-based handlers (auth.py) with new class-based handlers (handler.py).
Both implementations are tested against the same expected response format.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from aiohttp import web
from aiohttp.typedefs import Handler, Middleware

from ai.backend.manager.api import auth_legacy as legacy_auth
from ai.backend.manager.api.auth import AuthAPIHandler
from ai.backend.manager.data.auth.types import AuthorizationResult, SSHKeypair
from ai.backend.manager.dto.context import ProcessorsCtx, RequestCtx
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.services.auth.actions.authorize import AuthorizeActionResult
from ai.backend.manager.services.auth.actions.generate_ssh_keypair import (
    GenerateSSHKeypairActionResult,
)
from ai.backend.manager.services.auth.actions.get_role import GetRoleActionResult
from ai.backend.manager.services.auth.actions.get_ssh_keypair import GetSSHKeypairActionResult
from ai.backend.manager.services.auth.actions.signup import SignupActionResult

# ==============================================================================
# Common Fixtures
# ==============================================================================


@pytest.fixture
def mock_processors() -> MagicMock:
    """Create mock processors with auth-related action processors."""
    processors = MagicMock()
    processors.auth = MagicMock()
    processors.auth.authorize = MagicMock()
    processors.auth.get_role = MagicMock()
    processors.auth.signup = MagicMock()
    processors.auth.signout = MagicMock()
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
def mock_root_context(mock_processors: MagicMock) -> MagicMock:
    """Create mock RootContext."""
    root_ctx = MagicMock()
    root_ctx.processors = mock_processors
    return root_ctx


@pytest.fixture
def auth_middleware(
    mock_user_data: dict[str, Any], mock_keypair_data: dict[str, Any]
) -> Middleware:
    """Create middleware that sets authentication context."""

    @web.middleware
    async def middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
        request["user"] = mock_user_data
        request["keypair"] = mock_keypair_data
        request["is_authorized"] = True
        request["is_admin"] = False
        request["is_superadmin"] = False
        return await handler(request)

    return middleware


# ==============================================================================
# Legacy App Fixture (function-based handlers from auth.py)
# ==============================================================================


@pytest.fixture
def legacy_app(
    auth_middleware: Middleware,
    mock_root_context: MagicMock,
) -> web.Application:
    """Create aiohttp app with legacy function-based auth handlers."""
    app = web.Application(middlewares=[auth_middleware])
    app["_root.context"] = mock_root_context

    # Register legacy handlers
    app.router.add_get("/auth", legacy_auth.test)
    app.router.add_post("/auth", legacy_auth.test)
    app.router.add_get("/auth/test", legacy_auth.test)
    app.router.add_post("/auth/test", legacy_auth.test)
    app.router.add_post("/auth/authorize", legacy_auth.authorize)
    app.router.add_get("/auth/role", legacy_auth.get_role)
    app.router.add_post("/auth/signup", legacy_auth.signup)
    app.router.add_post("/auth/signout", legacy_auth.signout)
    app.router.add_post("/auth/update-password-no-auth", legacy_auth.update_password_no_auth)
    app.router.add_post("/auth/update-password", legacy_auth.update_password)
    app.router.add_post("/auth/update-full-name", legacy_auth.update_full_name)
    app.router.add_get("/auth/ssh-keypair", legacy_auth.get_ssh_keypair)
    app.router.add_patch("/auth/ssh-keypair", legacy_auth.generate_ssh_keypair)
    app.router.add_post("/auth/ssh-keypair", legacy_auth.upload_ssh_keypair)

    return app


# ==============================================================================
# New App Fixture (class-based handlers from handler.py)
# ==============================================================================


@pytest.fixture
def new_handler() -> AuthAPIHandler:
    """Create AuthAPIHandler instance."""
    return AuthAPIHandler()


@pytest.fixture
def new_app(
    new_handler: AuthAPIHandler,
    auth_middleware: Middleware,
    mock_root_context: MagicMock,
) -> web.Application:
    """Create aiohttp app with new class-based auth handlers."""
    app = web.Application(middlewares=[auth_middleware])
    app["_root.context"] = mock_root_context

    # Register new handlers
    app.router.add_get("/auth", new_handler.verify_auth)
    app.router.add_post("/auth", new_handler.verify_auth)
    app.router.add_get("/auth/test", new_handler.verify_auth)
    app.router.add_post("/auth/test", new_handler.verify_auth)
    app.router.add_post("/auth/authorize", new_handler.authorize)
    app.router.add_get("/auth/role", new_handler.get_role)
    app.router.add_post("/auth/signup", new_handler.signup)
    app.router.add_post("/auth/signout", new_handler.signout)
    app.router.add_post("/auth/update-password-no-auth", new_handler.update_password_no_auth)
    app.router.add_post("/auth/update-password", new_handler.update_password)
    app.router.add_post("/auth/update-full-name", new_handler.update_full_name)
    app.router.add_get("/auth/ssh-keypair", new_handler.get_ssh_keypair)
    app.router.add_patch("/auth/ssh-keypair", new_handler.generate_ssh_keypair)
    app.router.add_post("/auth/ssh-keypair", new_handler.upload_ssh_keypair)

    return app


@pytest.fixture
def patch_middleware_params(mock_processors: MagicMock) -> tuple[Any, Any]:
    """Patch MiddlewareParam.from_request methods to return mocks for new handlers."""

    async def mock_processors_ctx_from_request(_cls: Any, request: web.Request) -> MagicMock:
        ctx = MagicMock()
        ctx.processors = mock_processors
        return ctx

    async def mock_request_ctx_from_request(_cls: Any, request: web.Request) -> MagicMock:
        ctx = MagicMock()
        ctx.request = request
        return ctx

    return (
        patch.object(
            ProcessorsCtx,
            "from_request",
            classmethod(mock_processors_ctx_from_request),
        ),
        patch.object(
            RequestCtx,
            "from_request",
            classmethod(mock_request_ctx_from_request),
        ),
    )


# ==============================================================================
# Regression Tests: Compare Legacy vs New Response Formats
# ==============================================================================


class TestAuthorizeRegression:
    """Compare authorize endpoint responses between legacy and new handlers."""

    @pytest.fixture
    def authorize_action_result(self, user_uuid: Any) -> AuthorizeActionResult:
        """Create authorize action result for testing."""
        return AuthorizeActionResult(
            stream_response=None,
            authorization_result=AuthorizationResult(
                user_id=user_uuid,
                access_key="TESTKEY123",
                secret_key="TESTSECRET456",
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
            ),
        )

    @pytest.mark.asyncio
    async def test_authorize_response_format_compatibility(
        self,
        aiohttp_client: Any,
        legacy_app: web.Application,
        new_app: web.Application,
        mock_processors: MagicMock,
        authorize_action_result: AuthorizeActionResult,
        patch_middleware_params: tuple[Any, Any],
    ) -> None:
        """Verify legacy and new handlers produce identical response formats."""
        mock_processors.auth.authorize.wait_for_complete = AsyncMock(
            return_value=authorize_action_result
        )

        request_body = {
            "type": "keypair",
            "domain": "default",
            "username": "test@example.com",
            "password": "testpass",
        }

        # Get legacy response
        legacy_client = await aiohttp_client(legacy_app)
        legacy_resp = await legacy_client.post("/auth/authorize", json=request_body)
        legacy_data = await legacy_resp.json()

        # Get new response
        processors_ctx_patch, request_ctx_patch = patch_middleware_params
        with processors_ctx_patch, request_ctx_patch:
            new_client = await aiohttp_client(new_app)
            new_resp = await new_client.post("/auth/authorize", json=request_body)
            new_data = await new_resp.json()

        # Compare
        assert legacy_resp.status == new_resp.status
        assert legacy_data == new_data


class TestGetRoleRegression:
    """Compare get_role endpoint responses between legacy and new handlers."""

    @pytest.fixture
    def get_role_action_result(self) -> GetRoleActionResult:
        """Create get_role action result for testing."""
        return GetRoleActionResult(
            global_role="user",
            domain_role="admin",
            group_role="manager",
        )

    @pytest.mark.asyncio
    async def test_get_role_response_format_compatibility(
        self,
        aiohttp_client: Any,
        legacy_app: web.Application,
        new_app: web.Application,
        mock_processors: MagicMock,
        get_role_action_result: GetRoleActionResult,
        patch_middleware_params: tuple[Any, Any],
    ) -> None:
        """Verify legacy and new handlers produce identical response formats."""
        mock_processors.auth.get_role.wait_for_complete = AsyncMock(
            return_value=get_role_action_result
        )

        # Get legacy response
        legacy_client = await aiohttp_client(legacy_app)
        legacy_resp = await legacy_client.get("/auth/role")
        legacy_data = await legacy_resp.json()

        # Get new response
        processors_ctx_patch, request_ctx_patch = patch_middleware_params
        with processors_ctx_patch, request_ctx_patch:
            new_client = await aiohttp_client(new_app)
            new_resp = await new_client.get("/auth/role")
            new_data = await new_resp.json()

        # Compare
        assert legacy_resp.status == new_resp.status
        assert legacy_data == new_data


class TestSignupRegression:
    """Compare signup endpoint responses between legacy and new handlers."""

    @pytest.fixture
    def signup_action_result(self) -> SignupActionResult:
        """Create signup action result for testing."""
        return SignupActionResult(
            user_id=uuid4(),
            access_key="NEWKEY123",
            secret_key="NEWSECRET456",
        )

    @pytest.mark.asyncio
    async def test_signup_response_format_compatibility(
        self,
        aiohttp_client: Any,
        legacy_app: web.Application,
        new_app: web.Application,
        mock_processors: MagicMock,
        signup_action_result: SignupActionResult,
        patch_middleware_params: tuple[Any, Any],
    ) -> None:
        """Verify legacy and new handlers produce identical response formats."""
        mock_processors.auth.signup.wait_for_complete = AsyncMock(return_value=signup_action_result)

        request_body = {
            "domain": "default",
            "email": "newuser@example.com",
            "password": "securepass",
        }

        # Get legacy response
        legacy_client = await aiohttp_client(legacy_app)
        legacy_resp = await legacy_client.post("/auth/signup", json=request_body)
        legacy_data = await legacy_resp.json()

        # Get new response
        processors_ctx_patch, request_ctx_patch = patch_middleware_params
        with processors_ctx_patch, request_ctx_patch:
            new_client = await aiohttp_client(new_app)
            new_resp = await new_client.post("/auth/signup", json=request_body)
            new_data = await new_resp.json()

        # Compare
        assert legacy_resp.status == new_resp.status
        assert legacy_data == new_data


class TestSSHKeypairRegression:
    """Compare SSH keypair endpoint responses between legacy and new handlers."""

    @pytest.fixture
    def get_ssh_keypair_result(self) -> GetSSHKeypairActionResult:
        """Create get_ssh_keypair result for testing."""
        return GetSSHKeypairActionResult(public_key="ssh-rsa AAAAB3...")

    @pytest.fixture
    def generate_ssh_keypair_result(self) -> GenerateSSHKeypairActionResult:
        """Create generate_ssh_keypair result for testing."""
        return GenerateSSHKeypairActionResult(
            ssh_keypair=SSHKeypair(
                ssh_public_key="ssh-rsa AAAAB3...",
                ssh_private_key="-----BEGIN RSA PRIVATE KEY-----\n...",
            )
        )

    @pytest.mark.asyncio
    async def test_get_ssh_keypair_response_compatibility(
        self,
        aiohttp_client: Any,
        legacy_app: web.Application,
        new_app: web.Application,
        mock_processors: MagicMock,
        get_ssh_keypair_result: GetSSHKeypairActionResult,
        patch_middleware_params: tuple[Any, Any],
    ) -> None:
        """Verify legacy and new get_ssh_keypair produce identical responses."""
        mock_processors.auth.get_ssh_keypair.wait_for_complete = AsyncMock(
            return_value=get_ssh_keypair_result
        )

        # Get legacy response
        legacy_client = await aiohttp_client(legacy_app)
        legacy_resp = await legacy_client.get("/auth/ssh-keypair")
        legacy_data = await legacy_resp.json()

        # Get new response
        processors_ctx_patch, request_ctx_patch = patch_middleware_params
        with processors_ctx_patch, request_ctx_patch:
            new_client = await aiohttp_client(new_app)
            new_resp = await new_client.get("/auth/ssh-keypair")
            new_data = await new_resp.json()

        # Compare
        assert legacy_resp.status == new_resp.status
        assert legacy_data == new_data

    @pytest.mark.asyncio
    async def test_generate_ssh_keypair_response_compatibility(
        self,
        aiohttp_client: Any,
        legacy_app: web.Application,
        new_app: web.Application,
        mock_processors: MagicMock,
        generate_ssh_keypair_result: GenerateSSHKeypairActionResult,
        patch_middleware_params: tuple[Any, Any],
    ) -> None:
        """Verify legacy and new generate_ssh_keypair produce identical responses."""
        mock_processors.auth.generate_ssh_keypair.wait_for_complete = AsyncMock(
            return_value=generate_ssh_keypair_result
        )

        # Get legacy response
        legacy_client = await aiohttp_client(legacy_app)
        legacy_resp = await legacy_client.patch("/auth/ssh-keypair")
        legacy_data = await legacy_resp.json()

        # Get new response
        processors_ctx_patch, request_ctx_patch = patch_middleware_params
        with processors_ctx_patch, request_ctx_patch:
            new_client = await aiohttp_client(new_app)
            new_resp = await new_client.patch("/auth/ssh-keypair")
            new_data = await new_resp.json()

        # Compare
        assert legacy_resp.status == new_resp.status
        assert legacy_data == new_data
