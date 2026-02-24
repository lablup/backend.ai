from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import pytest
import sqlalchemy as sa
import yarl
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.group import association_groups_users
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.user import users


@dataclass
class SecondUserFixtureData:
    user_uuid: uuid.UUID
    access_key: str
    secret_key: str


@pytest.fixture()
async def second_user_fixture(
    db_engine: SAEngine,
    group_fixture: uuid.UUID,
    domain_fixture: str,
    resource_policy_fixture: str,
) -> AsyncIterator[SecondUserFixtureData]:
    """Insert a second regular user for multi-user integration tests."""
    unique_id = secrets.token_hex(4)
    email = f"user2-{unique_id}@test.local"
    data = SecondUserFixtureData(
        user_uuid=uuid.uuid4(),
        access_key=f"AKTEST{secrets.token_hex(7).upper()}",
        secret_key=secrets.token_hex(20),
    )
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(users).values(
                uuid=str(data.user_uuid),
                username=f"user2-{unique_id}",
                email=email,
                password=PasswordInfo(
                    password=secrets.token_urlsafe(8),
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=600_000,
                    salt_size=32,
                ),
                need_password_change=False,
                full_name=f"Second User {unique_id}",
                description=f"Test second user {unique_id}",
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
async def second_user_registry(
    server_factory: Any,
    second_user_fixture: SecondUserFixtureData,
) -> AsyncIterator[BackendAIClientRegistry]:
    """Create a BackendAIClientRegistry authenticated as the second user."""
    registry = await BackendAIClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server_factory.url)),
        HMACAuth(
            access_key=second_user_fixture.access_key,
            secret_key=second_user_fixture.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()
