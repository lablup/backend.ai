"""
Component test fixtures for the OpenID Connect plugin.

Provides:
  - Mock fixtures for external OpenID Provider HTTP endpoints
    (discovery, JWKS, token exchange) and JWT signing utilities.
  - Real PostgreSQL database (Docker) with Alembic schema.
  - Real Valkey/Redis (Docker) for session storage.
  - Aiohttp app mocks wired to real infrastructure.
"""

from __future__ import annotations

import asyncio
import secrets
import tempfile
import textwrap
import time
import uuid
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from urllib.parse import quote_plus as urlquote

import jwt as pyjwt
import pytest
import sqlalchemy as sa
from authlib.jose import JsonWebKey  # pants: no-infer-dep
from authlib.jose import jwt as jose_jwt  # pants: no-infer-dep
from sqlalchemy.ext.asyncio import create_async_engine

from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import (
    ResourceSlot,
    ValkeyProfileTarget,
    ValkeyTarget,
    VFolderHostPermissionMap,
)
from ai.backend.logging import LogLevel
from ai.backend.manager.cli.context import CLIContext
from ai.backend.manager.cli.dbschema import oneshot as cli_schema_oneshot
from ai.backend.manager.config.unified import DatabaseConfig
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.models.base import pgsql_connect_opts
from ai.backend.manager.models.domain import domains
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.group import association_groups_users, groups
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.resource_policy import (
    DefaultForUnspecified,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
    keypair_resource_policies,
    project_resource_policies,
    user_resource_policies,
)
from ai.backend.manager.models.user import UserRole, UserStatus, users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, connect_database
from ai.backend.manager.plugin.openid.hook import OIDCHookPlugin
from ai.backend.manager.plugin.openid.valkey_client import ValkeyOpenIDClient
from ai.backend.manager.plugin.openid.webapp import OIDCWebAppPlugin
from ai.backend.testutils.bootstrap import (  # noqa: F401
    postgres_container,
    redis_container,
)

# ===========================================================================
# OpenID Provider mock fixtures
# ===========================================================================

IDP_ISSUER = "https://idp.example.com"


# ---------------------------------------------------------------------------
# RSA key pair / JWKS
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def oidc_rsa_key() -> dict[str, Any]:
    """RSA private key used by the mock IdP to sign ID tokens."""
    key = JsonWebKey.generate_key("RSA", 2048, is_private=True)
    key_dict: dict[str, Any] = key.as_dict(is_private=True)
    key_dict.update({"kid": "test-key-1", "use": "sig", "alg": "RS256"})
    return key_dict


@pytest.fixture(scope="session")
def oidc_jwks(oidc_rsa_key: dict[str, Any]) -> dict[str, Any]:
    """JWKS (public keys only) served by the mock IdP's jwks_uri endpoint."""
    private_fields = {"d", "p", "q", "dp", "dq", "qi"}
    public_key = {k: v for k, v in oidc_rsa_key.items() if k not in private_fields}
    return {"keys": [public_key]}


# ---------------------------------------------------------------------------
# OIDC discovery document
# ---------------------------------------------------------------------------


@pytest.fixture
def oidc_discovery() -> dict[str, Any]:
    """OpenID Connect discovery document (.well-known/openid-configuration)."""
    return {
        "issuer": IDP_ISSUER,
        "authorization_endpoint": f"{IDP_ISSUER}/authorize",
        "token_endpoint": f"{IDP_ISSUER}/token",
        "jwks_uri": f"{IDP_ISSUER}/.well-known/jwks.json",
        "userinfo_endpoint": f"{IDP_ISSUER}/userinfo",
        "response_types_supported": ["code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "scopes_supported": ["openid", "profile", "email"],
    }


# ---------------------------------------------------------------------------
# Plugin config
# ---------------------------------------------------------------------------


@pytest.fixture
def plugin_config() -> dict[str, Any]:
    """Plugin configuration as stored in etcd."""
    return {
        "openid": {
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
            "well_known": f"{IDP_ISSUER}/.well-known/openid-configuration",
            "group_mapping": {
                "backend-ai-users": {
                    "domain": "default",
                    "project": "default",
                    "user_resource_policy": "default",
                    "keypair_resource_policy": "default",
                },
            },
            "group_order": "backend-ai-users",
        },
        "login_uri": "https://app.example.com/login",
        "secret": "test-jwt-secret-for-stoken",
    }


# ---------------------------------------------------------------------------
# ID token creation
# ---------------------------------------------------------------------------


@pytest.fixture
def oidc_id_token_claims() -> dict[str, Any]:
    """Standard claims for a valid OIDC ID token."""
    now = int(time.time())
    return {
        "iss": IDP_ISSUER,
        "sub": "idp-user-subject-001",
        "aud": "test-client-id",
        "exp": now + 3600,
        "iat": now,
        "nonce": "test-nonce-value",
        "email": "alice@example.com",
        "name": "Alice Example",
        "groups": ["backend-ai-users"],
    }


@pytest.fixture
def sign_id_token(oidc_rsa_key: dict[str, Any]) -> Callable[..., str]:
    """Factory: sign arbitrary claims into a JWT using the mock IdP's RSA key."""

    def _sign(claims: dict[str, Any]) -> str:
        header = {"alg": "RS256", "kid": oidc_rsa_key["kid"]}
        token_bytes = jose_jwt.encode(header, claims, oidc_rsa_key)
        return token_bytes.decode("utf-8") if isinstance(token_bytes, bytes) else token_bytes

    return _sign


@pytest.fixture
def oidc_token_response(
    sign_id_token: Callable[..., str], oidc_id_token_claims: dict[str, Any]
) -> dict[str, Any]:
    """Complete token response from the IdP's token endpoint."""
    return {
        "access_token": "mock-access-token-xyz",
        "token_type": "Bearer",
        "expires_in": 3600,
        "id_token": sign_id_token(oidc_id_token_claims),
        "scope": "openid profile email",
    }


# ---------------------------------------------------------------------------
# HTTP mocks — OpenID Provider endpoints
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_aiohttp_session(oidc_discovery: dict[str, Any], oidc_jwks: dict[str, Any]) -> MagicMock:
    """
    Mock aiohttp.ClientSession that routes GET requests to:
      - /.well-known/openid-configuration  ->  discovery document
      - /.well-known/jwks.json             ->  JWKS
    """

    def _make_ctx(data: dict[str, Any]) -> MagicMock:
        resp = MagicMock()
        resp.json = AsyncMock(return_value=data)
        resp.status = 200
        resp.__aenter__ = AsyncMock(return_value=resp)
        resp.__aexit__ = AsyncMock(return_value=False)
        return resp

    def _route(url: Any, **kwargs: Any) -> MagicMock:
        url_str = str(url)
        if "openid-configuration" in url_str:
            return _make_ctx(oidc_discovery)
        if "jwks" in url_str:
            return _make_ctx(oidc_jwks)
        return _make_ctx({})

    session = MagicMock()
    session.get = MagicMock(side_effect=_route)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    return session


@pytest.fixture
def mock_oauth2_client(oidc_token_response: dict[str, Any]) -> MagicMock:
    """
    Mock authlib AsyncOAuth2Client:
      - create_authorization_url -> deterministic redirect URL
      - fetch_token              -> token response with a real signed id_token
    """
    client = MagicMock()
    client.create_authorization_url = MagicMock(
        return_value=(
            f"{IDP_ISSUER}/authorize?client_id=test-client-id&state=mock-state",
            "mock-state",
        )
    )
    client.fetch_token = AsyncMock(return_value=oidc_token_response)
    return client


# ===========================================================================
# Real infrastructure fixtures (PostgreSQL, Valkey)
# ===========================================================================

# ---------------------------------------------------------------------------
# Database — session-scoped setup
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def test_db() -> str:
    """Unique database name for the test session."""
    return f"test_openid_{secrets.token_hex(8)}"


@pytest.fixture(scope="session")
def db_config(postgres_container: Any, test_db: str) -> DatabaseConfig:  # noqa: F811
    """DatabaseConfig pointing at the Docker PostgreSQL container."""
    _, addr = postgres_container
    return DatabaseConfig(
        type="postgresql",
        addr=HostPortPairModel(host=addr.host, port=addr.port),
        name=test_db,
        user="postgres",
        password="develove",
        pool_size=4,
        pool_recycle=-1,
        pool_pre_ping=False,
        max_overflow=4,
        lock_conn_timeout=0,
    )


@pytest.fixture(scope="session")
def database(request: pytest.FixtureRequest, db_config: DatabaseConfig, test_db: str) -> Any:
    """
    Create the test database and install the schema via Alembic oneshot.
    Must be synchronous because cli_schema_oneshot internally calls asyncio.run().
    """
    addr = db_config.addr
    address = f"{addr.host}:{addr.port}"
    user = db_config.user or "postgres"
    password = db_config.password or ""
    bootstrap_url = f"postgresql+asyncpg://{urlquote(user)}:{urlquote(password)}@{address}/testing"

    # 1. Create the test database.
    async def _create() -> None:
        engine = create_async_engine(
            bootstrap_url,
            connect_args=pgsql_connect_opts,
            isolation_level="AUTOCOMMIT",
        )
        while True:
            try:
                async with engine.connect() as conn:
                    await conn.execute(sa.text(f'CREATE DATABASE "{test_db}";'))
            except (ConnectionError, OSError):
                await asyncio.sleep(0.1)
                continue
            else:
                break
        await engine.dispose()

    asyncio.run(_create())

    # 2. Run Alembic oneshot to create all tables.
    alembic_cfg_template = textwrap.dedent("""\
    [alembic]
    script_location = ai.backend.manager.models:alembic
    sqlalchemy.url = {url}

    [loggers]
    keys = root
    [logger_root]
    level = WARNING
    handlers = console
    [handlers]
    keys = console
    [handler_console]
    class = StreamHandler
    args = (sys.stdout,)
    formatter = simple
    level = WARNING
    [formatters]
    keys = simple
    [formatter_simple]
    format = [%(name)s] %(message)s
    """)

    sa_url = f"postgresql+asyncpg://{user}:{password}@{address}/{test_db}"
    cli_ctx = CLIContext(config_path=None, log_level=LogLevel.DEBUG)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf8",
        suffix=".ini",
        delete=False,
    ) as f:
        f.write(alembic_cfg_template.format(url=sa_url))
        f.flush()
        cfg_path = f.name

    click_ctx = cli_schema_oneshot.make_context("test", ["-f", cfg_path], obj=cli_ctx)
    cli_schema_oneshot.invoke(click_ctx)
    Path(cfg_path).unlink(missing_ok=True)

    yield

    # 3. Drop the test database.
    async def _drop() -> None:
        engine = create_async_engine(
            bootstrap_url,
            connect_args=pgsql_connect_opts,
            isolation_level="AUTOCOMMIT",
        )
        async with engine.connect() as conn:
            await conn.execute(sa.text(f'REVOKE CONNECT ON DATABASE "{test_db}" FROM public;'))
            await conn.execute(
                sa.text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE pid <> pg_backend_pid();"
                )
            )
            await conn.execute(sa.text(f'DROP DATABASE "{test_db}";'))
        await engine.dispose()

    request.addfinalizer(lambda: asyncio.run(_drop()))


# ---------------------------------------------------------------------------
# Database engine — function-scoped
# ---------------------------------------------------------------------------


@pytest.fixture
async def database_engine(
    db_config: DatabaseConfig, database: Any
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    """Live ExtendedAsyncSAEngine connected to the test database."""
    async with connect_database(db_config) as db:
        yield db


# ---------------------------------------------------------------------------
# Seed data — minimum rows required by FK constraints
# ---------------------------------------------------------------------------


@pytest.fixture
async def seed_data(
    database_engine: ExtendedAsyncSAEngine,
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    """
    Insert the minimum seed data that the openid plugin's DB operations
    require (domain, resource policies, group).
    Yields the database_engine for convenience.
    """
    async with database_engine.begin_session() as sess:
        sess.add(DomainRow(name="default", total_resource_slots=ResourceSlot({})))
        sess.add(
            UserResourcePolicyRow(
                name="default",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
        )
        sess.add(
            ProjectResourcePolicyRow(
                name="default",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
        )
        conn = await sess.connection()
        await conn.execute(
            keypair_resource_policies.insert().values(
                name="default",
                default_for_unspecified=DefaultForUnspecified.LIMITED,
                total_resource_slots=ResourceSlot({}),
                max_session_lifetime=0,
                max_concurrent_sessions=30,
                max_pending_session_count=None,
                max_pending_session_resource_slots=None,
                max_concurrent_sftp_sessions=1,
                max_containers_per_session=1,
                idle_timeout=1800,
                allowed_vfolder_hosts=VFolderHostPermissionMap({}),
            )
        )
        sess.add(
            GroupRow(
                name="default",
                domain_name="default",
                total_resource_slots=ResourceSlot({}),
                resource_policy="default",
            )
        )
        await sess.flush()

    yield database_engine

    # Teardown — delete in FK-safe order.
    async with database_engine.begin_session() as sess:
        conn = await sess.connection()
        await conn.execute(association_groups_users.delete())
        await conn.execute(keypairs.delete())
        await conn.execute(users.delete())
        await conn.execute(groups.delete())
        await conn.execute(keypair_resource_policies.delete())
        await conn.execute(project_resource_policies.delete())
        await conn.execute(user_resource_policies.delete())
        await conn.execute(domains.delete())


# ---------------------------------------------------------------------------
# Valkey client — real connection
# ---------------------------------------------------------------------------


@pytest.fixture
async def valkey_client(redis_container: Any) -> AsyncIterator[ValkeyOpenIDClient]:  # noqa: F811
    """Real ValkeyOpenIDClient connected to the Docker Redis container."""
    _, addr = redis_container
    target = ValkeyTarget(addr=f"{addr.host}:{addr.port}")
    client = await ValkeyOpenIDClient.create(target, db_id=8)
    yield client
    await client.close()


# ---------------------------------------------------------------------------
# Config provider mock (uses real Redis addr)
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_config_provider(redis_container: Any) -> MagicMock:  # noqa: F811
    """
    Mock config_provider with:
      - config.auth.password_hash_* attributes
      - config.redis.to_valkey_profile_target() -> real ValkeyProfileTarget
    """
    _, addr = redis_container
    provider = MagicMock()
    provider.config.auth.password_hash_algorithm = "bcrypt"
    provider.config.auth.password_hash_rounds = 12
    provider.config.auth.password_hash_salt_size = 16
    provider.config.redis.to_valkey_profile_target.return_value = ValkeyProfileTarget(
        addr=f"{addr.host}:{addr.port}",
    )
    return provider


# ---------------------------------------------------------------------------
# Aiohttp app mock — wires real DB + mock config_provider
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_root_app(
    seed_data: ExtendedAsyncSAEngine, mock_config_provider: MagicMock
) -> dict[str, Any]:
    """
    Dict simulating root_app that plugin handlers access via
    request.app["_root_app"]["_db"] / ["_config_provider"].
    """
    return {
        "_db": seed_data,  # seed_data yields database_engine
        "_config_provider": mock_config_provider,
    }


# ===========================================================================
# Plugin instance fixtures
# ===========================================================================


@pytest.fixture
def hook_plugin(plugin_config: dict[str, Any]) -> OIDCHookPlugin:
    """OIDCHookPlugin instance."""
    return OIDCHookPlugin(plugin_config, local_config={})


@pytest.fixture
def webapp_plugin(plugin_config: dict[str, Any]) -> OIDCWebAppPlugin:
    """OIDCWebAppPlugin instance."""
    return OIDCWebAppPlugin(plugin_config, local_config={})


# ===========================================================================
# Factory fixtures (callables)
# ===========================================================================


@pytest.fixture
def insert_user(seed_data: ExtendedAsyncSAEngine) -> Callable[..., Any]:
    """Async callable(email, status) -> uuid. Inserts a minimal user row."""

    async def _insert(
        email: str = "alice@example.com",
        status: UserStatus = UserStatus.ACTIVE,
    ) -> uuid.UUID:
        user_uuid = uuid.uuid4()
        async with seed_data.begin_session() as sess:
            conn = await sess.connection()
            await conn.execute(
                users.insert().values(
                    uuid=user_uuid,
                    username=email,
                    email=email,
                    password=PasswordInfo(
                        password="placeholder-password",
                        algorithm=PasswordHashAlgorithm.BCRYPT,
                        rounds=4,
                        salt_size=16,
                    ),
                    need_password_change=False,
                    full_name="Test User",
                    description="",
                    status=status,
                    status_info="test",
                    domain_name="default",
                    role=UserRole.USER,
                    resource_policy="default",
                )
            )
        return user_uuid

    return _insert


@pytest.fixture
def make_stoken(plugin_config: dict[str, Any]) -> Callable[..., str]:
    """Callable(user_uuid, email, *, expired) -> str. Creates an HS256 sToken JWT."""
    secret = plugin_config["secret"]

    def _make(
        user_uuid: uuid.UUID,
        email: str,
        *,
        expired: bool = False,
    ) -> str:
        now = int(time.time())
        payload: dict[str, Any] = {
            "user": str(user_uuid),
            "email": email,
        }
        if expired:
            payload["exp"] = now - 3600
        else:
            payload["exp"] = now + 3600
        return pyjwt.encode(payload, secret, algorithm="HS256")

    return _make


@pytest.fixture
def make_hook_request(seed_data: ExtendedAsyncSAEngine) -> Callable[..., MagicMock]:
    """Callable(cookies) -> mock Request with _root_app wired to seed_data."""
    root_app: dict[str, Any] = {"_db": seed_data}

    def _make(cookies: dict[str, str]) -> MagicMock:
        request = MagicMock()
        request.cookies = cookies
        request.app = {"_root_app": root_app}
        return request

    return _make


# ===========================================================================
# Data fixtures (shared across test_hook and test_webapp)
# ===========================================================================


@pytest.fixture
def password_info() -> PasswordInfo:
    """PasswordInfo instance for user creation tests."""
    return PasswordInfo(
        password="random-test-password",
        algorithm=PasswordHashAlgorithm.BCRYPT,
        rounds=12,
        salt_size=16,
    )


@pytest.fixture
def openid_claims() -> dict[str, Any]:
    """Standard OpenID claims dict for user creation tests."""
    return {
        "email": "newuser@example.com",
        "name": "New User",
        "groups": ["backend-ai-users"],
    }


@pytest.fixture
def group_mapping() -> dict[str, Any]:
    """Single-group mapping dict."""
    return {
        "backend-ai-users": {
            "domain": "default",
            "project": "default",
            "user_resource_policy": "default",
            "keypair_resource_policy": "default",
        },
    }


# ===========================================================================
# Webapp handler test fixtures
# ===========================================================================


@pytest.fixture
def failing_oauth2_client() -> MagicMock:
    """Mock OAuth2Client whose fetch_token raises an Exception."""
    client = MagicMock()
    client.fetch_token = AsyncMock(side_effect=Exception("token exchange failed"))
    return client
