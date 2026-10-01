"""Component tests for OIDCWebAppPlugin, utility functions, and Valkey session."""

from __future__ import annotations

import base64
import hashlib
import urllib.parse
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import jwt as pyjwt
import pytest
import sqlalchemy as sa
import yarl
from authlib.integrations.base_client.errors import OAuthError  # pants: no-infer-dep
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import rsa

from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair.row import keypairs
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.plugin.openid.exceptions import InvalidSession, OpenIDGroupNotAllowed
from ai.backend.manager.plugin.openid.valkey_client import ValkeyOpenIDClient
from ai.backend.manager.plugin.openid.webapp import (
    OIDCWebAppPlugin,
    create_user_if_not_exists,
    generate_user_data,
)
from ai.backend.manager.repositories.auth.repository import AuthRepository

from .conftest import ClientCertificate

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
        with pytest.raises(OpenIDGroupNotAllowed):
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
        auth_repository: AuthRepository,
        openid_claims: dict[str, Any],
        group_mapping: dict[str, Any],
        password_info: PasswordInfo,
    ) -> None:
        user_id = await create_user_if_not_exists(
            openid_claims,
            group_mapping,
            ["backend-ai-users"],
            auth_repository,
            password_info,
        )

        async with seed_data.begin_readonly_session() as sess:
            user_row = await sess.scalar(sa.select(UserRow).where(UserRow.uuid == user_id))
            assert user_row is not None
            assert user_row.email == "newuser@example.com"
            assert user_row.full_name == "New User"

            # Verify keypair was created
            conn = await sess.connection()
            row = (
                await conn.execute(sa.select(keypairs).where(keypairs.c.user == user_id))
            ).fetchone()
            assert row is not None
            assert row.is_default is True

    async def test_returns_existing_user_without_duplicate(
        self,
        seed_data: ExtendedAsyncSAEngine,
        auth_repository: AuthRepository,
        openid_claims: dict[str, Any],
        group_mapping: dict[str, Any],
        password_info: PasswordInfo,
    ) -> None:
        user_id1 = await create_user_if_not_exists(
            openid_claims,
            group_mapping,
            ["backend-ai-users"],
            auth_repository,
            password_info,
        )
        user_id2 = await create_user_if_not_exists(
            openid_claims,
            group_mapping,
            ["backend-ai-users"],
            auth_repository,
            password_info,
        )

        assert user_id1 == user_id2

        # Verify only one keypair exists
        async with seed_data.begin_readonly_session() as sess:
            conn = await sess.connection()
            count = (
                await conn.execute(
                    sa.select(sa.func.count())
                    .select_from(keypairs)
                    .where(keypairs.c.user == user_id1)
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
            "openid.token_endpoint": "https://idp.example.com/token",
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

        assert response.status == 302
        redirect_url = response.headers["Location"]
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

        assert response.status == 302
        location = response.headers["Location"]
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

    async def _redirect(
        self, plugin: OIDCWebAppPlugin, request: MagicMock, client: MagicMock
    ) -> yarl.URL:
        with patch(
            "ai.backend.manager.plugin.openid.webapp.AsyncOAuth2Client",
            return_value=client,
        ):
            response = await plugin.redirect(request)
        assert response.status == 302
        return yarl.URL(response.headers["Location"])

    @pytest.mark.parametrize(
        ("provider_error", "bai_error"),
        [
            ("access_denied", "openid-access-denied"),
            ("consent_required", "openid-access-denied"),
            ("temporarily_unavailable", "openid-provider-unavailable"),
            ("invalid_scope", "openid-provider-misconfigured"),
            ("unknown_error", "openid-not-authenticated"),
        ],
    )
    async def test_redirect_callback_error_returns_with_error(
        self,
        webapp_plugin: OIDCWebAppPlugin,
        redirect_request: MagicMock,
        mock_oauth2_client: MagicMock,
        provider_error: str,
        bai_error: str,
    ) -> None:
        redirect_request.query = {
            "state": redirect_request.query["state"],
            "error": provider_error,
            "error_description": "AADSTS00000: provider detail",
        }

        location = await self._redirect(webapp_plugin, redirect_request, mock_oauth2_client)

        assert location.host == "app.example.com"
        assert location.query["bai_error"] == bai_error
        assert "sToken" not in location.query
        assert "provider detail" not in str(location)
        mock_oauth2_client.fetch_token.assert_not_called()

    @pytest.mark.parametrize(
        ("token_error", "bai_error"),
        [
            (OAuthError(error="invalid_client"), "openid-provider-misconfigured"),
            (OAuthError(error="invalid_grant"), "invalid-openid-session"),
            (OAuthError(error="server_error"), "openid-provider-unavailable"),
            (httpx.ConnectError("connection refused"), "openid-provider-unavailable"),
            (RuntimeError("unexpected"), "internal-server-error"),
        ],
    )
    async def test_redirect_token_exchange_error_returns_with_error(
        self,
        webapp_plugin: OIDCWebAppPlugin,
        redirect_request: MagicMock,
        mock_oauth2_client: MagicMock,
        token_error: Exception,
        bai_error: str,
    ) -> None:
        mock_oauth2_client.fetch_token = AsyncMock(side_effect=token_error)

        location = await self._redirect(webapp_plugin, redirect_request, mock_oauth2_client)

        assert location.query["bai_error"] == bai_error
        assert "sToken" not in location.query

    async def test_redirect_group_not_allowed_returns_with_error(
        self,
        plugin_config: dict[str, Any],
        redirect_request: MagicMock,
        mock_oauth2_client: MagicMock,
    ) -> None:
        openid = {**plugin_config["openid"], "group_order": "other-group"}
        openid["group_mapping"] = {"other-group": {"domain": "default"}}
        plugin = OIDCWebAppPlugin({**plugin_config, "openid": openid}, local_config={})

        location = await self._redirect(plugin, redirect_request, mock_oauth2_client)

        assert location.query["bai_error"] == "openid-group-not-allowed"
        assert "sToken" not in location.query

    async def test_redirect_expired_session_returns_with_error(
        self,
        webapp_plugin: OIDCWebAppPlugin,
        redirect_request: MagicMock,
        mock_oauth2_client: MagicMock,
    ) -> None:
        redirect_request.query = {
            "state": urllib.parse.urlencode({
                "redirect": "https://app.example.com/dashboard",
                "session": str(uuid.uuid4()),
            }),
            "code": "auth-code-123",
        }

        location = await self._redirect(webapp_plugin, redirect_request, mock_oauth2_client)

        assert location.query["bai_error"] == "invalid-openid-session"
        mock_oauth2_client.fetch_token.assert_not_called()

    async def test_redirect_without_state_returns_to_login_uri(
        self,
        webapp_plugin: OIDCWebAppPlugin,
        redirect_request: MagicMock,
        mock_oauth2_client: MagicMock,
    ) -> None:
        redirect_request.query = {"code": "auth-code-123"}

        location = await self._redirect(webapp_plugin, redirect_request, mock_oauth2_client)

        assert str(location.with_query(None)) == "https://app.example.com/login"
        assert location.query["bai_error"] == "invalid-openid-session"
        mock_oauth2_client.fetch_token.assert_not_called()


# ===========================================================================
# TestOAuth2ClientAuthentication — token request client authentication
# ===========================================================================


class TestOAuth2ClientAuthentication:
    TOKEN_ENDPOINT = "https://idp.example.com/token"

    def _prepare_token_request(self, plugin: OIDCWebAppPlugin) -> dict[str, str]:
        client = plugin._create_oauth2_client(self.TOKEN_ENDPOINT)
        auth = client.client_auth(client.token_endpoint_auth_method)
        _, _, body = auth.prepare("POST", self.TOKEN_ENDPOINT, {}, "grant_type=authorization_code")
        return dict(urllib.parse.parse_qsl(body))

    def test_private_key_signs_client_assertion(
        self,
        private_key_plugin_config: dict[str, Any],
        client_certificate: ClientCertificate,
    ) -> None:
        plugin = OIDCWebAppPlugin(private_key_plugin_config, local_config={})

        form = self._prepare_token_request(plugin)

        assert form["client_assertion_type"] == (
            "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
        )
        assertion = form["client_assertion"]
        header = pyjwt.get_unverified_header(assertion)
        thumbprint = hashlib.sha256(client_certificate.certificate_der).digest()
        assert header["alg"] == "PS256"
        assert header["typ"] == "JWT"
        assert header["x5t#S256"] == base64.urlsafe_b64encode(thumbprint).rstrip(b"=").decode()
        public_key = x509.load_pem_x509_certificate(
            client_certificate.certificate.encode()
        ).public_key()
        assert isinstance(public_key, rsa.RSAPublicKey)
        claims = pyjwt.decode(
            assertion, public_key, algorithms=["PS256"], audience=self.TOKEN_ENDPOINT
        )
        assert claims["iss"] == "test-client-id"
        assert claims["sub"] == "test-client-id"
        assert claims["jti"]
        assert claims["nbf"] <= claims["exp"] <= claims["nbf"] + 300

    def test_client_secret_keeps_basic_authentication(
        self, webapp_plugin: OIDCWebAppPlugin
    ) -> None:
        client = webapp_plugin._create_oauth2_client(self.TOKEN_ENDPOINT)

        assert client.token_endpoint_auth_method == "client_secret_basic"
        assert client.client_secret == "test-client-secret"
