"""
Tests for SessionRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime

import pytest
from dateutil.tz import tzutc

from ai.backend.common.types import (
    AccessKey,
    BinarySize,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import (
    PasswordHashAlgorithm,
    PasswordInfo,
    UserRole,
    UserRow,
    UserStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.testutils.db import with_tables


class TestSessionRepositorySearch:
    """Test cases for SessionRepository.search"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created."""
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                GroupRow,
                KeyPairRow,
                SessionRow,
                KernelRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test domain and return domain name"""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain for session",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.commit()

        return domain_name

    @pytest.fixture
    async def test_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test scaling group and return name"""
        scaling_group_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            scaling_group = ScalingGroupRow(
                name=scaling_group_name,
                description="Test scaling group",
                is_active=True,
                is_public=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts={},
            )
            db_sess.add(scaling_group)
            await db_sess.commit()

        return scaling_group_name

    @pytest.fixture
    async def test_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test resource policy and return policy name"""
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(policy)
            await db_sess.commit()

        return policy_name

    @pytest.fixture
    async def test_keypair_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test keypair resource policy and return policy name"""
        policy_name = f"test-kp-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = KeyPairResourcePolicyRow(
                name=policy_name,
                max_session_lifetime=0,
                max_concurrent_sessions=10,
                max_concurrent_sftp_sessions=5,
                max_pending_session_count=5,
                max_pending_session_resource_slots={},
                total_resource_slots={},
            )
            db_sess.add(policy)
            await db_sess.commit()

        return policy_name

    @pytest.fixture
    async def test_user_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_resource_policy_name: str,
    ) -> uuid.UUID:
        """Create test user and return user UUID"""
        user_uuid = uuid.uuid4()

        password_info = PasswordInfo(
            password="dummy",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=600_000,
            salt_size=32,
        )

        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                username=f"testuser-{user_uuid.hex[:8]}",
                email=f"test-{user_uuid.hex[:8]}@example.com",
                password=password_info,
                need_password_change=False,
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=test_domain_name,
                role=UserRole.USER,
                resource_policy=test_resource_policy_name,
            )
            db_sess.add(user)
            await db_sess.commit()

        return user_uuid

    @pytest.fixture
    async def test_group_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
    ) -> uuid.UUID:
        """Create test group and return group ID"""
        group_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            group = GroupRow(
                id=group_id,
                name=f"test-group-{group_id.hex[:8]}",
                description="Test group for session",
                is_active=True,
                domain_name=test_domain_name,
                total_resource_slots={},
                allowed_vfolder_hosts={},
            )
            db_sess.add(group)
            await db_sess.commit()

        return group_id

    @pytest.fixture
    async def test_access_key(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user_id: uuid.UUID,
        test_keypair_resource_policy_name: str,
    ) -> AccessKey:
        """Create test keypair and return access key"""
        access_key = AccessKey(f"AKTEST{uuid.uuid4().hex[:14].upper()}")

        async with db_with_cleanup.begin_session() as db_sess:
            keypair = KeyPairRow(
                user_id=test_user_id,
                access_key=access_key,
                secret_key=f"secret-{uuid.uuid4().hex}",
                is_active=True,
                is_admin=False,
                resource_policy=test_keypair_resource_policy_name,
                rate_limit=1000,
                num_queries=0,
                concurrency_used=0,
            )
            db_sess.add(keypair)
            await db_sess.commit()

        return access_key

    @pytest.fixture
    def session_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> SessionRepository:
        """Create SessionRepository instance with database"""
        return SessionRepository(db=db_with_cleanup)

    async def _create_session(
        self,
        db: ExtendedAsyncSAEngine,
        domain_name: str,
        group_id: uuid.UUID,
        user_uuid: uuid.UUID,
        access_key: AccessKey,
        scaling_group_name: str,
        session_name: str,
        session_type: SessionTypes = SessionTypes.INTERACTIVE,
        status: SessionStatus = SessionStatus.RUNNING,
    ) -> SessionId:
        """Helper to create a session directly in the database"""
        session_id = SessionId(uuid.uuid4())

        async with db.begin_session() as db_sess:
            session = SessionRow(
                id=session_id,
                creation_id=f"creation-{session_id.hex[:8]}",
                name=session_name,
                session_type=session_type,
                priority=0,
                cluster_mode=ClusterMode.SINGLE_NODE.name,
                cluster_size=1,
                domain_name=domain_name,
                group_id=group_id,
                user_uuid=user_uuid,
                access_key=access_key,
                scaling_group_name=scaling_group_name,
                occupying_slots=ResourceSlot({"cpu": "1", "mem": "1073741824"}),
                requested_slots=ResourceSlot({"cpu": "1", "mem": "1073741824"}),
                status=status,
                status_info=None,
                result=SessionResult.UNDEFINED,
                num_queries=0,
                created_at=datetime.now(tzutc()),
                use_host_network=False,
            )
            db_sess.add(session)
            await db_sess.commit()

        return session_id

    # =========================================================================
    # Tests - Search with pagination
    # =========================================================================

    @pytest.mark.asyncio
    async def test_search_sessions_offset_pagination_first_page(
        self,
        session_repository: SessionRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_group_id: uuid.UUID,
        test_user_id: uuid.UUID,
        test_access_key: AccessKey,
        test_scaling_group_name: str,
    ) -> None:
        """Test first page of offset-based pagination"""
        # Create 15 sessions
        for i in range(15):
            await self._create_session(
                db_with_cleanup,
                test_domain_name,
                test_group_id,
                test_user_id,
                test_access_key,
                test_scaling_group_name,
                session_name=f"test-session-{i:02d}",
            )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await session_repository.search(querier=querier)

        assert len(result.items) == 10
        assert result.total_count == 15

    @pytest.mark.asyncio
    async def test_search_sessions_offset_pagination_second_page(
        self,
        session_repository: SessionRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_group_id: uuid.UUID,
        test_user_id: uuid.UUID,
        test_access_key: AccessKey,
        test_scaling_group_name: str,
    ) -> None:
        """Test second page of offset-based pagination"""
        # Create 15 sessions
        for i in range(15):
            await self._create_session(
                db_with_cleanup,
                test_domain_name,
                test_group_id,
                test_user_id,
                test_access_key,
                test_scaling_group_name,
                session_name=f"test-session-{i:02d}",
            )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[],
            orders=[],
        )

        result = await session_repository.search(querier=querier)

        assert len(result.items) == 5
        assert result.total_count == 15

    @pytest.mark.asyncio
    async def test_search_sessions_empty_result(
        self,
        session_repository: SessionRepository,
    ) -> None:
        """Test searching when no sessions exist"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await session_repository.search(querier=querier)

        assert len(result.items) == 0
        assert result.total_count == 0
        assert result.has_next_page is False
        assert result.has_previous_page is False

    # =========================================================================
    # Tests - Search with filtering
    # =========================================================================

    @pytest.mark.asyncio
    async def test_search_sessions_filter_by_status(
        self,
        session_repository: SessionRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_group_id: uuid.UUID,
        test_user_id: uuid.UUID,
        test_access_key: AccessKey,
        test_scaling_group_name: str,
    ) -> None:
        """Test searching sessions filtered by status"""
        # Create sessions with different statuses
        await self._create_session(
            db_with_cleanup,
            test_domain_name,
            test_group_id,
            test_user_id,
            test_access_key,
            test_scaling_group_name,
            session_name="running-session",
            status=SessionStatus.RUNNING,
        )
        await self._create_session(
            db_with_cleanup,
            test_domain_name,
            test_group_id,
            test_user_id,
            test_access_key,
            test_scaling_group_name,
            session_name="pending-session",
            status=SessionStatus.PENDING,
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                lambda: SessionRow.status == SessionStatus.RUNNING,
            ],
            orders=[],
        )

        result = await session_repository.search(querier=querier)

        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.items[0].status == SessionStatus.RUNNING

    @pytest.mark.asyncio
    async def test_search_sessions_filter_by_session_type(
        self,
        session_repository: SessionRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_group_id: uuid.UUID,
        test_user_id: uuid.UUID,
        test_access_key: AccessKey,
        test_scaling_group_name: str,
    ) -> None:
        """Test searching sessions filtered by session type"""
        # Create sessions with different types
        await self._create_session(
            db_with_cleanup,
            test_domain_name,
            test_group_id,
            test_user_id,
            test_access_key,
            test_scaling_group_name,
            session_name="interactive-session",
            session_type=SessionTypes.INTERACTIVE,
        )
        await self._create_session(
            db_with_cleanup,
            test_domain_name,
            test_group_id,
            test_user_id,
            test_access_key,
            test_scaling_group_name,
            session_name="batch-session",
            session_type=SessionTypes.BATCH,
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                lambda: SessionRow.session_type == SessionTypes.BATCH,
            ],
            orders=[],
        )

        result = await session_repository.search(querier=querier)

        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.items[0].session_type == SessionTypes.BATCH

    # =========================================================================
    # Tests - Search with ordering
    # =========================================================================

    @pytest.mark.asyncio
    async def test_search_sessions_order_by_name_ascending(
        self,
        session_repository: SessionRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_group_id: uuid.UUID,
        test_user_id: uuid.UUID,
        test_access_key: AccessKey,
        test_scaling_group_name: str,
    ) -> None:
        """Test searching sessions ordered by name ascending"""
        names = ["charlie", "alpha", "bravo"]
        for name in names:
            await self._create_session(
                db_with_cleanup,
                test_domain_name,
                test_group_id,
                test_user_id,
                test_access_key,
                test_scaling_group_name,
                session_name=name,
            )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[SessionRow.name.asc()],
        )

        result = await session_repository.search(querier=querier)

        result_names = [s.name for s in result.items if s.name is not None]
        assert result_names == sorted(result_names)
        assert result_names[0] == "alpha"
        assert result_names[-1] == "charlie"

    @pytest.mark.asyncio
    async def test_search_sessions_order_by_name_descending(
        self,
        session_repository: SessionRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_group_id: uuid.UUID,
        test_user_id: uuid.UUID,
        test_access_key: AccessKey,
        test_scaling_group_name: str,
    ) -> None:
        """Test searching sessions ordered by name descending"""
        names = ["charlie", "alpha", "bravo"]
        for name in names:
            await self._create_session(
                db_with_cleanup,
                test_domain_name,
                test_group_id,
                test_user_id,
                test_access_key,
                test_scaling_group_name,
                session_name=name,
            )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[SessionRow.name.desc()],
        )

        result = await session_repository.search(querier=querier)

        result_names = [s.name for s in result.items if s.name is not None]
        assert result_names == sorted(result_names, reverse=True)
        assert result_names[0] == "charlie"
        assert result_names[-1] == "alpha"

    # =========================================================================
    # Tests - Search with combined query
    # =========================================================================

    @pytest.mark.asyncio
    async def test_search_sessions_with_pagination_filter_and_order(
        self,
        session_repository: SessionRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_group_id: uuid.UUID,
        test_user_id: uuid.UUID,
        test_access_key: AccessKey,
        test_scaling_group_name: str,
    ) -> None:
        """Test searching sessions with pagination, filter condition, and ordering combined"""
        # Create 10 RUNNING sessions
        for i in range(10):
            await self._create_session(
                db_with_cleanup,
                test_domain_name,
                test_group_id,
                test_user_id,
                test_access_key,
                test_scaling_group_name,
                session_name=f"running-{i:02d}",
                status=SessionStatus.RUNNING,
            )

        # Create 5 PENDING sessions
        for i in range(5):
            await self._create_session(
                db_with_cleanup,
                test_domain_name,
                test_group_id,
                test_user_id,
                test_access_key,
                test_scaling_group_name,
                session_name=f"pending-{i:02d}",
                status=SessionStatus.PENDING,
            )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=5, offset=2),
            conditions=[
                lambda: SessionRow.status == SessionStatus.RUNNING,
            ],
            orders=[SessionRow.name.asc()],
        )

        result = await session_repository.search(querier=querier)

        # Should return only RUNNING sessions
        assert result.total_count == 10
        assert len(result.items) == 5

        # All results should be RUNNING
        for session in result.items:
            assert session.status == SessionStatus.RUNNING

        # Results should be ordered by name
        result_names = [s.name for s in result.items if s.name is not None]
        assert result_names == sorted(result_names)
