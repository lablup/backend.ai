from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest
import sqlalchemy as sa
import yarl
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.rest.auth.handler import AuthHandler
from ai.backend.manager.api.rest.auth.registry import register_auth_routes

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
from ai.backend.manager.api.rest.middleware import auth as _auth_api
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.group import association_groups_users
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.user import users
from ai.backend.manager.services.auth.processors import AuthProcessors

_AUTH_SERVER_SUBAPP_MODULES = (_auth_api,)


@dataclass
class AuthUserFixtureData:
    """Extended user fixture that retains the raw password for auth tests."""

    user_uuid: uuid.UUID
    access_key: str
    secret_key: str
    password: str
    email: str
    domain_name: str


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps, auth_processors: AuthProcessors
) -> list[RouteRegistry]:
    """Load only the auth module for auth-domain tests."""
    return [
        register_auth_routes(AuthHandler(auth=auth_processors), route_deps),
    ]


@pytest.fixture()
async def auth_user_fixture(
    db_engine: SAEngine,
    group_fixture: uuid.UUID,
    domain_fixture: str,
    resource_policy_fixture: str,
) -> AsyncIterator[AuthUserFixtureData]:
    """Insert a regular user with a known password for auth tests.

    Unlike the parent conftest's user fixtures, this one retains the raw
    password so that tests can call authorize, signout, and update_password.
    """
    unique_id = secrets.token_hex(4)
    email = f"auth-user-{unique_id}@test.local"
    password = f"TestP@ss{unique_id}"
    data = AuthUserFixtureData(
        user_uuid=uuid.uuid4(),
        access_key=f"AKTEST{secrets.token_hex(7).upper()}",
        secret_key=secrets.token_hex(20),
        password=password,
        email=email,
        domain_name=domain_fixture,
    )
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(users).values(
                uuid=str(data.user_uuid),
                username=f"auth-user-{unique_id}",
                email=email,
                password=PasswordInfo(
                    password=password,
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=600_000,
                    salt_size=32,
                ),
                need_password_change=False,
                full_name=f"Auth User {unique_id}",
                description=f"Test auth user {unique_id}",
                status=UserStatus.ACTIVE,
                status_info="admin-requested",
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
                role=UserRole.USER,
            )
        )
        await conn.execute(
            sa.insert(keypairs).values(
                user_id=email,
                access_key=data.access_key,
                secret_key=data.secret_key,
                is_active=True,
                resource_policy=resource_policy_fixture,
                rate_limit=30000,
                num_queries=0,
                is_admin=False,
                user=str(data.user_uuid),
            )
        )
        await conn.execute(
            sa.insert(association_groups_users).values(
                group_id=str(group_fixture),
                user_id=str(data.user_uuid),
            )
        )
    yield data
    async with db_engine.begin() as conn:
        await conn.execute(
            association_groups_users.delete().where(
                association_groups_users.c.user_id == str(data.user_uuid)
            )
        )
        await conn.execute(keypairs.delete().where(keypairs.c.access_key == data.access_key))
        await conn.execute(users.delete().where(users.c.uuid == str(data.user_uuid)))


@pytest.fixture()
async def auth_user_registry(
    server: Any,
    auth_user_fixture: AuthUserFixtureData,
) -> AsyncIterator[BackendAIClientRegistry]:
    """Create a BackendAIClientRegistry authenticated as the auth user."""
    registry = await BackendAIClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=auth_user_fixture.access_key,
            secret_key=auth_user_fixture.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()


@asynccontextmanager
async def _create_auth_user(
    db_engine: SAEngine,
    *,
    group_id: uuid.UUID,
    domain_name: str,
    resource_policy: str,
    email_prefix: str,
    username_prefix: str,
    full_name_prefix: str,
    description_prefix: str,
    status: UserStatus,
    extra_user_values: dict[str, Any] | None = None,
) -> AsyncIterator[AuthUserFixtureData]:
    """Shared helper that inserts a user + keypair + group membership, then cleans up."""
    unique_id = secrets.token_hex(4)
    email = f"{email_prefix}-{unique_id}@test.local"
    password = f"TestP@ss{unique_id}"
    data = AuthUserFixtureData(
        user_uuid=uuid.uuid4(),
        access_key=f"AKTEST{secrets.token_hex(7).upper()}",
        secret_key=secrets.token_hex(20),
        password=password,
        email=email,
        domain_name=domain_name,
    )
    user_values: dict[str, Any] = {
        "uuid": str(data.user_uuid),
        "username": f"{username_prefix}-{unique_id}",
        "email": email,
        "password": PasswordInfo(
            password=password,
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=600_000,
            salt_size=32,
        ),
        "need_password_change": False,
        "full_name": f"{full_name_prefix} {unique_id}",
        "description": f"{description_prefix} {unique_id}",
        "status": status,
        "status_info": "admin-requested",
        "domain_name": domain_name,
        "resource_policy": resource_policy,
        "role": UserRole.USER,
    }
    if extra_user_values:
        user_values.update(extra_user_values)
    async with db_engine.begin() as conn:
        await conn.execute(sa.insert(users).values(**user_values))
        await conn.execute(
            sa.insert(keypairs).values(
                user_id=email,
                access_key=data.access_key,
                secret_key=data.secret_key,
                is_active=True,
                resource_policy=resource_policy,
                rate_limit=30000,
                num_queries=0,
                is_admin=False,
                user=str(data.user_uuid),
            )
        )
        await conn.execute(
            sa.insert(association_groups_users).values(
                group_id=str(group_id),
                user_id=str(data.user_uuid),
            )
        )
    yield data
    async with db_engine.begin() as conn:
        await conn.execute(
            association_groups_users.delete().where(
                association_groups_users.c.user_id == str(data.user_uuid)
            )
        )
        await conn.execute(keypairs.delete().where(keypairs.c.access_key == data.access_key))
        await conn.execute(users.delete().where(users.c.uuid == str(data.user_uuid)))


@pytest.fixture()
async def inactive_user_fixture(
    db_engine: SAEngine,
    group_fixture: uuid.UUID,
    domain_fixture: str,
    resource_policy_fixture: str,
) -> AsyncIterator[AuthUserFixtureData]:
    """Insert a user with INACTIVE status for authorization rejection tests."""
    async with _create_auth_user(
        db_engine,
        group_id=group_fixture,
        domain_name=domain_fixture,
        resource_policy=resource_policy_fixture,
        email_prefix="auth-inactive",
        username_prefix="auth-inactive",
        full_name_prefix="Inactive User",
        description_prefix="Test inactive user",
        status=UserStatus.INACTIVE,
    ) as data:
        yield data


@pytest.fixture()
async def before_verification_user_fixture(
    db_engine: SAEngine,
    group_fixture: uuid.UUID,
    domain_fixture: str,
    resource_policy_fixture: str,
) -> AsyncIterator[AuthUserFixtureData]:
    """Insert a user with BEFORE_VERIFICATION status for authorization rejection tests."""
    async with _create_auth_user(
        db_engine,
        group_id=group_fixture,
        domain_name=domain_fixture,
        resource_policy=resource_policy_fixture,
        email_prefix="auth-unverified",
        username_prefix="auth-unverified",
        full_name_prefix="Unverified User",
        description_prefix="Test unverified user",
        status=UserStatus.BEFORE_VERIFICATION,
    ) as data:
        yield data


@pytest.fixture()
async def expired_password_user_fixture(
    db_engine: SAEngine,
    group_fixture: uuid.UUID,
    domain_fixture: str,
    resource_policy_fixture: str,
) -> AsyncIterator[AuthUserFixtureData]:
    """Insert a user whose password_changed_at is far in the past for expiry tests."""
    async with _create_auth_user(
        db_engine,
        group_id=group_fixture,
        domain_name=domain_fixture,
        resource_policy=resource_policy_fixture,
        email_prefix="auth-expired",
        username_prefix="auth-expired",
        full_name_prefix="Expired Pass User",
        description_prefix="Test expired password user",
        status=UserStatus.ACTIVE,
        extra_user_values={"password_changed_at": datetime(2020, 1, 1, tzinfo=UTC)},
    ) as data:
        yield data
