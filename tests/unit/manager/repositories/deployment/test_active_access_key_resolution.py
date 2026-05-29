from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.types import AccessKey, ResourceSlot
from ai.backend.manager.errors.deployment import (
    NoActiveKeypairForDeployment,
    UserNotFoundInDeployment,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.deployment.db_source.db_source import DeploymentDBSource
from ai.backend.testutils.db import with_tables


@dataclass
class KeypairSpec:
    access_key: str
    is_active: bool
    created_at: datetime
    is_main: bool = False


@dataclass
class UserSeed:
    user_uuid: uuid.UUID
    domain_name: str
    main_access_key: str | None
    keypairs: list[KeypairSpec]


class TestResolveUserAndActiveAccessKey:
    """Tests for DeploymentDBSource._resolve_user_and_active_access_key.

    The resolver is the load-bearing piece of BA-6241: sokovan deployment
    replicas were persisting non-deterministic and potentially inactive
    access keys into sessions.access_key. The contract under test is:

    1. A keypair matching users.main_access_key wins when active.
    2. Missing user vs no-active-keypair raise different exceptions.
    """

    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def db_source(self, db: ExtendedAsyncSAEngine) -> DeploymentDBSource:
        return DeploymentDBSource(
            db=db,
            storage_manager=MagicMock(spec=StorageSessionManager),
        )

    async def _seed(self, db: ExtendedAsyncSAEngine, spec: UserSeed) -> None:
        domain_name = spec.domain_name
        user_policy = f"user-policy-{uuid.uuid4().hex[:8]}"
        kp_policy = f"kp-policy-{uuid.uuid4().hex[:8]}"

        async with db.begin_session() as sess:
            sess.add(
                DomainRow(
                    name=domain_name,
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            sess.add(
                UserResourcePolicyRow(
                    name=user_policy,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            sess.add(
                KeyPairResourcePolicyRow(
                    name=kp_policy,
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=2,
                    max_containers_per_session=10,
                    idle_timeout=3600,
                )
            )
            await sess.flush()
            sess.add(
                UserRow(
                    uuid=spec.user_uuid,
                    username=f"user-{spec.user_uuid.hex[:8]}",
                    email=f"{spec.user_uuid.hex[:8]}@test.io",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy=user_policy,
                )
            )
            await sess.flush()
            for kp in spec.keypairs:
                sess.add(
                    KeyPairRow(
                        access_key=kp.access_key,
                        secret_key="secret",
                        user=spec.user_uuid,
                        is_active=kp.is_active,
                        resource_policy=kp_policy,
                        created_at=kp.created_at,
                    )
                )
            await sess.flush()
            if spec.main_access_key is not None:
                await sess.execute(
                    sa.update(UserRow)
                    .where(UserRow.uuid == spec.user_uuid)
                    .values(main_access_key=spec.main_access_key)
                )
            await sess.commit()

    async def _resolve(
        self, db_source: DeploymentDBSource, user_uuid: uuid.UUID
    ) -> AccessKey | type[Exception]:
        async with db_source._begin_readonly_session_read_committed() as sess:
            result = await db_source._resolve_user_and_active_access_key(sess, user_uuid)
        return result.access_key

    async def test_picks_main_access_key_when_active(
        self,
        db: ExtendedAsyncSAEngine,
        db_source: DeploymentDBSource,
    ) -> None:
        # main_access_key wins over a newer active key.
        user_uuid = uuid.uuid4()
        now = datetime.now(tz=UTC)
        main_key = "AK" + "M" * 18
        other_active = "AK" + "O" * 18
        await self._seed(
            db,
            UserSeed(
                user_uuid=user_uuid,
                domain_name=f"d-{uuid.uuid4().hex[:8]}",
                main_access_key=main_key,
                keypairs=[
                    KeypairSpec(main_key, is_active=True, created_at=now - timedelta(days=10)),
                    KeypairSpec(other_active, is_active=True, created_at=now),
                ],
            ),
        )

        chosen = await self._resolve(db_source, user_uuid)

        assert chosen == AccessKey(main_key)

    async def test_raises_no_active_keypair_when_all_inactive(
        self,
        db: ExtendedAsyncSAEngine,
        db_source: DeploymentDBSource,
    ) -> None:
        user_uuid = uuid.uuid4()
        now = datetime.now(tz=UTC)
        await self._seed(
            db,
            UserSeed(
                user_uuid=user_uuid,
                domain_name=f"d-{uuid.uuid4().hex[:8]}",
                main_access_key=None,
                keypairs=[
                    KeypairSpec("AK" + "X" * 18, is_active=False, created_at=now),
                ],
            ),
        )

        with pytest.raises(NoActiveKeypairForDeployment):
            await self._resolve(db_source, user_uuid)

    async def test_raises_user_not_found_for_unknown_uuid(
        self,
        db: ExtendedAsyncSAEngine,
        db_source: DeploymentDBSource,
    ) -> None:
        # No seeding — the user simply does not exist.
        unknown = uuid.uuid4()

        with pytest.raises(UserNotFoundInDeployment):
            await self._resolve(db_source, unknown)
