"""Admin SSH public key registration, run against a real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.types import AccessKey, ResourceSlot
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.resource_group.row import (
    ResourceGroupForKeypairsRow,
    ResourceGroupRow,
)
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
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


@dataclass(frozen=True)
class _KeypairWithSSHKeys:
    access_key: AccessKey
    ssh_private_key: str


class TestAdminUpdateSSHPublicKey:
    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ResourceGroupRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                ResourceGroupForKeypairsRow,
            ],
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
    async def keypair_with_ssh_keys(self, db: ExtendedAsyncSAEngine) -> _KeypairWithSSHKeys:
        user_id = uuid.uuid4()
        domain_id = DomainID(uuid.uuid4())
        domain_name = f"domain-{domain_id.hex[:8]}"
        user_policy_name = f"user-policy-{user_id.hex[:8]}"
        keypair_policy_name = f"keypair-policy-{user_id.hex[:8]}"
        access_key = AccessKey(f"AKIATEST{user_id.hex[:10]}")
        ssh_private_key = "-----BEGIN RSA PRIVATE KEY-----\nSTORED\n-----END RSA PRIVATE KEY-----"
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
                    name=user_policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            session.add(
                KeyPairResourcePolicyRow(
                    name=keypair_policy_name,
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=2,
                    max_containers_per_session=10,
                    idle_timeout=3600,
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
                    resource_policy=user_policy_name,
                    allowed_client_ip=None,
                    totp_key=None,
                    domain_id=domain_id,
                )
            )
            await session.flush()
            session.add(
                KeyPairRow(
                    access_key=access_key,
                    secret_key=SecretValue("test_secret_key"),
                    user=user_id,
                    is_active=True,
                    is_default=True,
                    resource_policy=keypair_policy_name,
                    ssh_public_key="ssh-rsa STORED",
                    ssh_private_key=ssh_private_key,
                )
            )
        return _KeypairWithSSHKeys(access_key=access_key, ssh_private_key=ssh_private_key)

    async def test_replaces_the_public_key_and_keeps_the_private_key(
        self,
        repository: UserRepository,
        db: ExtendedAsyncSAEngine,
        keypair_with_ssh_keys: _KeypairWithSSHKeys,
    ) -> None:
        await repository.admin_update_ssh_public_key(
            access_key=keypair_with_ssh_keys.access_key,
            ssh_public_key="ssh-rsa REGISTERED",
        )

        async with db.begin_readonly_session() as session:
            keypair = await session.scalar(
                sa.select(KeyPairRow).where(
                    KeyPairRow.access_key == keypair_with_ssh_keys.access_key
                )
            )
        assert keypair is not None
        assert keypair.ssh_public_key == "ssh-rsa REGISTERED"
        assert keypair.ssh_private_key == keypair_with_ssh_keys.ssh_private_key
