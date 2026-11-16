"""The default SSH keypair of a user, run against a real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow
from ai.backend.manager.models.ssh_keypair.row import SSHKeypairRow
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.resource_policy.provider import (
    ResourcePolicyOpsProvider,
)
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.db import with_tables


class TestDefaultSSHKeypair:
    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection, [DomainRow, UserResourcePolicyRow, UserRow, SSHKeypairRow]
        ):
            yield database_connection

    @pytest.fixture
    def repository(self, db: ExtendedAsyncSAEngine) -> UserRepository:
        return UserRepository(
            db=db,
            v2_ops_provider=V2DBOpsProvider(db),
            share_ops_provider=ShareOpsProvider(db),
            policy_ops_provider=ResourcePolicyOpsProvider(db),
            key_provider_pool=KeyProviderPool(
                providers=[], write_provider_type=KeyProviderType.PLAIN
            ),
        )

    @pytest.fixture
    async def user_id(self, db: ExtendedAsyncSAEngine) -> UserID:
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

    async def _keys(self, db: ExtendedAsyncSAEngine, user_id: UserID) -> list[tuple[str, bool]]:
        async with db.begin_readonly_session() as session:
            rows = await session.execute(
                sa.select(SSHKeypairRow.public_key, SSHKeypairRow.is_default).where(
                    SSHKeypairRow.user_id == user_id
                )
            )
            return [(row.public_key, row.is_default) for row in rows]

    async def test_replace_without_one_creates_the_default(
        self, repository: UserRepository, user_id: UserID
    ) -> None:
        await repository.replace_default_ssh_keypair(user_id, "pub-1", "priv-1")

        data = await repository.default_ssh_keypair(user_id)

        assert data is not None
        assert data.public_key == "pub-1"
        assert data.private_key == SecretValue("priv-1")

    async def test_replace_leaves_one_default_holding_the_new_keys(
        self, db: ExtendedAsyncSAEngine, repository: UserRepository, user_id: UserID
    ) -> None:
        await repository.replace_default_ssh_keypair(user_id, "pub-1", "priv-1")
        await repository.replace_default_ssh_keypair(user_id, "pub-2", "priv-2")

        assert await self._keys(db, user_id) == [("pub-2", True)]

    async def test_purge_removes_the_default(
        self, db: ExtendedAsyncSAEngine, repository: UserRepository, user_id: UserID
    ) -> None:
        await repository.replace_default_ssh_keypair(user_id, "pub-1", "priv-1")

        await repository.purge_default_ssh_keypair(user_id)

        assert await repository.default_ssh_keypair(user_id) is None
        assert await self._keys(db, user_id) == []
