"""A user with SSH keypairs in each state, run against a real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow
from ai.backend.manager.models.ssh_keypair.row import SSHKeypairRow
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ssh_keypair.repository import SSHKeypairRepository
from ai.backend.testutils.db import with_tables


@pytest.fixture
async def db(database_connection: ExtendedAsyncSAEngine) -> AsyncGenerator[ExtendedAsyncSAEngine]:
    async with with_tables(
        database_connection, [DomainRow, UserResourcePolicyRow, UserRow, SSHKeypairRow]
    ):
        yield database_connection


@pytest.fixture
def ops_provider(db: ExtendedAsyncSAEngine) -> V2DBOpsProvider:
    return V2DBOpsProvider(db)


@pytest.fixture
def repository(ops_provider: V2DBOpsProvider) -> SSHKeypairRepository:
    return SSHKeypairRepository(ops_provider)


@pytest.fixture
async def user_id(db: ExtendedAsyncSAEngine) -> UserID:
    user_id = UserID(uuid.uuid4())
    domain_id = DomainID(uuid.uuid4())
    domain_name = f"domain-{domain_id.hex[:8]}"
    policy_name = f"policy-{user_id.hex[:8]}"
    async with db.begin_session() as session:
        session.add(
            DomainRow(
                id=domain_id,
                name=domain_name,
                description="",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
                integration_id=None,
            )
        )
        session.add(
            UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
        )
        await session.flush()
        session.add(
            UserRow(
                uuid=user_id,
                username=f"user-{user_id.hex[:8]}",
                email=f"user-{user_id.hex[:8]}@example.com",
                password=None,
                need_password_change=False,
                full_name="",
                description="",
                status=UserStatus.ACTIVE,
                status_info="",
                domain_name=domain_name,
                role=UserRole.USER,
                resource_policy=policy_name,
                allowed_client_ip=None,
                totp_key=None,
                domain_id=domain_id,
            )
        )
    return user_id


@pytest.fixture
async def default_id(repository: SSHKeypairRepository, user_id: UserID) -> SSHKeypairID:
    return (await repository.upload(user_id, "pub-default")).id


@pytest.fixture
async def other_id(
    repository: SSHKeypairRepository, user_id: UserID, default_id: SSHKeypairID
) -> SSHKeypairID:
    return (await repository.upload(user_id, "pub-other")).id
