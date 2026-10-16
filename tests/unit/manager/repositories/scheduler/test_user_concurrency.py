"""``count_user_active_sessions`` counts what the scheduler's per-user concurrency check counts."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.types import AccessKey, SecretKey, SessionTypes
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.fixtures import DomainFixtureData

from .conftest import create_pending_session_with_kernels


class TestCountUserActiveSessions:
    @pytest.fixture
    def db_source(
        self, db_with_cleanup: ExtendedAsyncSAEngine, resource_slot_types: None
    ) -> ScheduleDBSource:
        return ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))

    async def _create_keypair(
        self, db: ExtendedAsyncSAEngine, user_uuid: uuid.UUID, resource_policy: str
    ) -> AccessKey:
        access_key = AccessKey(f"AKIA{uuid.uuid4().hex[:16].upper()}")
        async with db.begin_session() as db_sess:
            db_sess.add(
                KeyPairRow(
                    access_key=access_key,
                    secret_key=SecretValue(SecretKey(f"SK{uuid.uuid4().hex}")),
                    is_active=True,
                    is_admin=False,
                    resource_policy=resource_policy,
                    rate_limit=1000,
                    num_queries=0,
                    user=user_uuid,
                )
            )
        return access_key

    @pytest.fixture
    async def second_access_key(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user_uuid: uuid.UUID,
        test_keypair_resource_policy_name: str,
    ) -> AccessKey:
        return await self._create_keypair(
            db_with_cleanup, test_user_uuid, test_keypair_resource_policy_name
        )

    @pytest.fixture
    async def other_user_access_key(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainFixtureData,
        test_user_resource_policy_name: str,
        test_keypair_resource_policy_name: str,
    ) -> tuple[uuid.UUID, AccessKey]:
        user_uuid = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                UserRow(
                    uuid=user_uuid,
                    email=f"other-{user_uuid.hex[:8]}@test.com",
                    username=f"other-{user_uuid.hex[:8]}",
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                    domain_name=test_domain.domain_name,
                    resource_policy=test_user_resource_policy_name,
                    domain_id=test_domain.domain_id,
                )
            )
        access_key = await self._create_keypair(
            db_with_cleanup, user_uuid, test_keypair_resource_policy_name
        )
        return user_uuid, access_key

    async def test_counts_sessions_of_every_keypair_once_each(
        self,
        db_source: ScheduleDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_domain: DomainFixtureData,
        test_scaling_group_id: ResourceGroupID,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        second_access_key: AccessKey,
        test_agent_id: str,
    ) -> None:
        """A two-kernel session counts as one, and both keypairs' sessions add up."""
        kernel = (test_agent_id, Decimal("1"), Decimal("1024"))
        for access_key, kernels in [
            (test_access_key, [kernel, kernel]),
            (second_access_key, [kernel]),
        ]:
            await create_pending_session_with_kernels(
                db_with_cleanup,
                domain_id=test_domain_id,
                domain_name=test_domain.domain_name,
                resource_group_id=test_scaling_group_id,
                resource_group_name=test_scaling_group_name,
                group_id=test_group_id,
                user_uuid=test_user_uuid,
                access_key=access_key,
                agent_assignments=kernels,
                session_status=SessionStatus.RUNNING,
                kernel_status=KernelStatus.RUNNING,
            )

        assert await db_source.count_user_active_sessions(UserID(test_user_uuid)) == 2

    @pytest.mark.parametrize(
        ("session_type", "session_status", "owned_by_other_user"),
        [
            (SessionTypes.SYSTEM, SessionStatus.RUNNING, False),
            (SessionTypes.INTERACTIVE, SessionStatus.PENDING, False),
            (SessionTypes.INTERACTIVE, SessionStatus.ERROR, False),
            (SessionTypes.INTERACTIVE, SessionStatus.TERMINATED, False),
            (SessionTypes.INTERACTIVE, SessionStatus.RUNNING, True),
        ],
        ids=["sftp", "pending", "error", "terminated", "other-user"],
    )
    async def test_skips_sessions_the_scheduler_does_not_count(
        self,
        db_source: ScheduleDBSource,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
        test_domain: DomainFixtureData,
        test_scaling_group_id: ResourceGroupID,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        other_user_access_key: tuple[uuid.UUID, AccessKey],
        test_agent_id: str,
        session_type: SessionTypes,
        session_status: SessionStatus,
        owned_by_other_user: bool,
    ) -> None:
        owner, access_key = (
            other_user_access_key if owned_by_other_user else (test_user_uuid, test_access_key)
        )
        await create_pending_session_with_kernels(
            db_with_cleanup,
            domain_id=test_domain_id,
            domain_name=test_domain.domain_name,
            resource_group_id=test_scaling_group_id,
            resource_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=owner,
            access_key=access_key,
            agent_assignments=[(test_agent_id, Decimal("1"), Decimal("1024"))],
            session_type=session_type,
            session_status=session_status,
        )

        assert await db_source.count_user_active_sessions(UserID(test_user_uuid)) == 0
