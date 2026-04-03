"""Component tests for OIDCWebAppPlugin, utility functions, and Valkey session."""

from __future__ import annotations

import urllib.parse
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import sqlalchemy as sa
from aiohttp import web

from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.plugin.openid.exceptions import InvalidSession
from ai.backend.manager.plugin.openid.valkey_client import ValkeyOpenIDClient
from ai.backend.manager.plugin.openid.webapp import (
    OIDCWebAppPlugin,
    OpenIDError,
    create_user_if_not_exists,
    generate_user_data,
)

# ===========================================================================
# TestGenerateUserData — pure function, no DB needed
# ===========================================================================


class TestGenerateUserData:
    @pytest.fixture
    def oidc_token(self) -> Any:
        def _make(groups: list[str]) -> dict[str, Any]:
            return {
                "email": "alice@example.com",
                "name": "Alice Example",
                "groups": groups,
            }

        return _make

    @pytest.fixture
    def multi_group_mapping(self) -> dict[str, Any]:
        return {
            "backend-ai-users": {
                "domain": "default",
                "project": "default",
                "user_resource_policy": "default",
                "keypair_resource_policy": "default",
            },
            "admins": {
                "domain": "admin-domain",
                "project": "admin-project",
                "user_resource_policy": "admin-rp",
                "keypair_resource_policy": "admin-kp",
            },
        }

    def test_valid_group_mapping(
        self, oidc_token: Any, multi_group_mapping: dict[str, Any]
    ) -> None:
        token = oidc_token(["backend-ai-users"])
        result = generate_user_data(token, multi_group_mapping, ["backend-ai-users"])

        assert result["user"]["username"] == "alice@example.com"
        assert result["user"]["email"] == "alice@example.com"
        assert result["user"]["full_name"] == "Alice Example"
        assert result["user"]["domain_name"] == "default"
        assert result["user"]["status"] == UserStatus.ACTIVE
        assert result["user"]["role"] == UserRole.USER
        assert result["project"] == "default"
        assert result["keypair_resource_policy"] == "default"
        assert result["user"]["password"]  # non-empty random string

    def test_no_matching_group_raises_error(
        self, oidc_token: Any, multi_group_mapping: dict[str, Any]
    ) -> None:
        token = oidc_token(["unknown-group"])
        with pytest.raises(OpenIDError, match="does not belong to group"):
            generate_user_data(token, multi_group_mapping, ["backend-ai-users"])

    def test_group_order_priority(
        self, oidc_token: Any, multi_group_mapping: dict[str, Any]
    ) -> None:
        token = oidc_token(["backend-ai-users", "admins"])
        # admins comes first in group_order -> picks admin mapping
        result = generate_user_data(token, multi_group_mapping, ["admins", "backend-ai-users"])
        assert result["user"]["domain_name"] == "admin-domain"
        assert result["project"] == "admin-project"

        # Reverse priority -> picks backend-ai-users mapping
        result2 = generate_user_data(token, multi_group_mapping, ["backend-ai-users", "admins"])
        assert result2["user"]["domain_name"] == "default"
        assert result2["project"] == "default"


# ===========================================================================
# TestCreateUserIfNotExists — real DB
# ===========================================================================


class TestCreateUserIfNotExists:
    async def test_creates_new_user_with_keypair(
        self,
        seed_data: ExtendedAsyncSAEngine,
        openid_claims: dict[str, Any],
        group_mapping: dict[str, Any],
        password_info: PasswordInfo,
    ) -> None:
        user = await create_user_if_not_exists(
            openid_claims,
            group_mapping,
            ["backend-ai-users"],
            seed_data,
            password_info,
        )

        assert user.email == "newuser@example.com"
        assert user.full_name == "New User"
        assert user.main_access_key is not None

        # Verify keypair was created
        async with seed_data.begin_readonly_session() as sess:
            conn = await sess.connection()
            row = (
                await conn.execute(sa.select(keypairs).where(keypairs.c.user == user.uuid))
            ).fetchone()
            assert row is not None
            assert row.access_key == user.main_access_key

    async def test_returns_existing_user_without_duplicate(
        self,
        seed_data: ExtendedAsyncSAEngine,
        openid_claims: dict[str, Any],
        group_mapping: dict[str, Any],
        password_info: PasswordInfo,
    ) -> None:
        user1 = await create_user_if_not_exists(
            openid_claims,
            group_mapping,
            ["backend-ai-users"],
            seed_data,
            password_info,
        )
        user2 = await create_user_if_not_exists(
            openid_claims,
            group_mapping,
            ["backend-ai-users"],
            seed_data,
            password_info,
        )

        assert user1.uuid == user2.uuid
        assert user1.email == user2.email

        # Verify only one keypair exists
        async with seed_data.begin_readonly_session() as sess:
            conn = await sess.connection()
            count = (
                await conn.execute(
                    sa.select(sa.func.count())
                    .select_from(keypairs)
                    .where(keypairs.c.user == user1.uuid)
                )
            ).scalar()
            assert count == 1


# ===========================================================================
# TestValkeySession — real Valkey
# ===========================================================================


class TestValkeySession:
    async def test_set_and_get_code_verifier(self, valkey_client: ValkeyOpenIDClient) -> None:
        session_key = str(uuid.uuid4())
        verifier = "test-code-verifier-abc123"

        await valkey_client.set_openid_key(session_key, verifier)
        result = await valkey_client.get_openid_key(session_key)
        assert result == verifier

    async def test_get_nonexistent_session_raises(self, valkey_client: ValkeyOpenIDClient) -> None:
        with pytest.raises(InvalidSession):
            await valkey_client.get_openid_key("nonexistent-session-key")


# ===========================================================================
# TestWebAppLogin — real Valkey, mock OAuth2Client
# ===========================================================================


class TestWebAppLogin:
    @pytest.fixture
    def login_request(self, valkey_client: ValkeyOpenIDClient) -> MagicMock:
        request = MagicMock()
        post_data = {"redirect_to": "https://app.example.com/dashboard"}
        request.post = AsyncMock(return_value=post_data)
        request.app = {
            "openid.authorization_endpoint": "https://idp.example.com/authorize",
            "valkey_client": valkey_client,
        }
        return request

    async def test_login_stores_verifier_and_redirects(
        self,
        webapp_plugin: OIDCWebAppPlugin,
        login_request: MagicMock,
        mock_oauth2_client: MagicMock,
    ) -> None:
        with patch(
            "ai.backend.manager.plugin.openid.webapp.AsyncOAuth2Client",
            return_value=mock_oauth2_client,
        ):
            response = await webapp_plugin.login(login_request)

        assert isinstance(response, web.HTTPFound)
        redirect_url = str(response.location)
        assert "idp.example.com/authorize" in redirect_url
        assert "client_id=test-client-id" in redirect_url

        mock_oauth2_client.create_authorization_url.assert_called_once()


# ===========================================================================
# TestWebAppRedirect — real DB + Valkey, mock OAuth2Client
# ===========================================================================


class TestWebAppRedirect:
    @pytest.fixture
    async def redirect_request(
        self,
        mock_root_app: dict[str, Any],
        valkey_client: ValkeyOpenIDClient,
        oidc_jwks: dict[str, Any],
    ) -> MagicMock:
        session_key = str(uuid.uuid4())
        await valkey_client.set_openid_key(session_key, "test-verifier")

        state = urllib.parse.urlencode({
            "redirect": "https://app.example.com/dashboard",
            "session": session_key,
        })

        request = MagicMock()
        request.query = {"state": state, "code": "auth-code-123"}
        request.url = (
            f"https://app.example.com/func/openid/redirect"
            f"?state={urllib.parse.quote(state)}&code=auth-code-123"
        )
        request.app = {
            "_root_app": mock_root_app,
            "openid.token_endpoint": "https://idp.example.com/token",
            "openid.jwks": oidc_jwks,
            "valkey_client": valkey_client,
        }
        return request

    async def test_redirect_creates_user_and_returns_stoken(
        self,
        webapp_plugin: OIDCWebAppPlugin,
        mock_root_app: dict[str, Any],
        redirect_request: MagicMock,
        mock_oauth2_client: MagicMock,
    ) -> None:
        with patch(
            "ai.backend.manager.plugin.openid.webapp.AsyncOAuth2Client",
            return_value=mock_oauth2_client,
        ):
            response = await webapp_plugin.redirect(redirect_request)

        assert isinstance(response, web.HTTPFound)
        location = str(response.location)
        assert "sToken=" in location
        assert "app.example.com/dashboard" in location

        # Verify user was created in DB
        db = mock_root_app["_db"]
        async with db.begin_readonly_session() as sess:
            result = await sess.execute(
                sa.select(UserRow).where(UserRow.email == "alice@example.com")
            )
            user = result.scalars().one_or_none()
            assert user is not None
            assert user.full_name == "Alice Example"

    async def test_redirect_invalid_token_returns_unauthorized(
        self,
        webapp_plugin: OIDCWebAppPlugin,
        redirect_request: MagicMock,
        failing_oauth2_client: MagicMock,
    ) -> None:
        with patch(
            "ai.backend.manager.plugin.openid.webapp.AsyncOAuth2Client",
            return_value=failing_oauth2_client,
        ):
            response = await webapp_plugin.redirect(redirect_request)

        assert response.status == 401
