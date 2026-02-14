"""
Tests for ResourceUsageHistoryRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.resource_usage_history import (
    DomainUsageBucketRow,
    KernelUsageRecordRow,
    ProjectUsageBucketRow,
    UsageBucketEntryRow,
    UserUsageBucketRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import (
    PasswordHashAlgorithm,
    PasswordInfo,
    UserRole,
    UserRow,
    UserStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, BulkCreator, Creator, Upserter
from ai.backend.manager.repositories.base.pagination import OffsetPagination
from ai.backend.manager.repositories.resource_usage_history import (
    DomainUsageBucketConditions,
    DomainUsageBucketCreatorSpec,
    DomainUsageBucketOrders,
    DomainUsageBucketUpserterSpec,
    KernelUsageRecordConditions,
    KernelUsageRecordCreatorSpec,
    KernelUsageRecordOrders,
    ProjectUsageBucketCreatorSpec,
    ResourceUsageHistoryRepository,
    UserUsageBucketCreatorSpec,
    UserUsageBucketUpserterSpec,
)
from ai.backend.testutils.db import with_tables


class TestResourceUsageHistoryRepository:
    """Test cases for ResourceUsageHistoryRepository"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                # Base rows in FK dependency order (parents before children)
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                AgentRow,
                ImageRow,
                SessionRow,
                KernelRow,
                ResourcePresetRow,
                # Resource Usage History rows (no FK constraints but need mapper registration)
                KernelUsageRecordRow,
                DomainUsageBucketRow,
                ProjectUsageBucketRow,
                UserUsageBucketRow,
                UsageBucketEntryRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_scaling_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test scaling group and return name"""
        sg_name = f"test-sg-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            sg = ScalingGroupRow(
                name=sg_name,
                description="Test scaling group for usage history",
                is_active=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
                wsproxy_addr=None,
            )
            db_sess.add(sg)
            await db_sess.commit()

        return sg_name

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
                description="Test domain for usage history",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.commit()

        return domain_name

    @pytest.fixture
    async def test_project_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
    ) -> uuid.UUID:
        """Create test project (group) and return its ID"""
        project_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            policy_name = f"test-project-policy-{uuid.uuid4().hex[:8]}"
            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_network_count=10,
            )
            db_sess.add(policy)
            await db_sess.flush()

            group = GroupRow(
                id=project_id,
                name=f"test-project-{project_id.hex[:8]}",
                domain_name=test_domain_name,
                description="Test project for usage history",
                resource_policy=policy_name,
            )
            db_sess.add(group)
            await db_sess.commit()

        return project_id

    @pytest.fixture
    async def test_user_uuid(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
    ) -> uuid.UUID:
        """Create test user and return user UUID"""
        user_uuid = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(policy)
            await db_sess.flush()

            password_info = PasswordInfo(
                password="dummy",
                algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                rounds=600_000,
                salt_size=32,
            )

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
                resource_policy=policy_name,
            )
            db_sess.add(user)
            await db_sess.commit()

        return user_uuid

    @pytest.fixture
    def resource_usage_history_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> ResourceUsageHistoryRepository:
        """Create ResourceUsageHistoryRepository instance with database"""
        return ResourceUsageHistoryRepository(db=db_with_cleanup)

    # ==================== Kernel Usage Record Tests ====================

    @pytest.mark.asyncio
    async def test_create_kernel_usage_record(
        self,
        resource_usage_history_repository: ResourceUsageHistoryRepository,
        test_scaling_group: str,
        test_domain_name: str,
        test_project_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
    ) -> None:
        """Test creating a single kernel usage record"""
        kernel_id = uuid.uuid4()
        session_id = uuid.uuid4()
        now = datetime.now(tz=UTC)

        creator = Creator(
            spec=KernelUsageRecordCreatorSpec(
                kernel_id=kernel_id,
                session_id=session_id,
                user_uuid=test_user_uuid,
                project_id=test_project_id,
                domain_name=test_domain_name,
                resource_group=test_scaling_group,
                period_start=now - timedelta(minutes=5),
                period_end=now,
                resource_usage=ResourceSlot({"cpu": Decimal("300"), "mem": Decimal("1073741824")}),
            )
        )

        result = await resource_usage_history_repository.create_kernel_usage_record(creator)

        assert result.kernel_id == kernel_id
        assert result.session_id == session_id
        assert result.user_uuid == test_user_uuid
        assert result.project_id == test_project_id
        assert result.resource_usage["cpu"] == Decimal("300")

    @pytest.mark.asyncio
    async def test_bulk_create_kernel_usage_records(
        self,
        resource_usage_history_repository: ResourceUsageHistoryRepository,
        test_scaling_group: str,
        test_domain_name: str,
        test_project_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
    ) -> None:
        """Test bulk creating kernel usage records"""
        now = datetime.now(tz=UTC)
        specs = []

        for i in range(5):
            kernel_id = uuid.uuid4()
            session_id = uuid.uuid4()
            period_start = now - timedelta(minutes=5 * (i + 1))
            period_end = now - timedelta(minutes=5 * i)

            specs.append(
                KernelUsageRecordCreatorSpec(
                    kernel_id=kernel_id,
                    session_id=session_id,
                    user_uuid=test_user_uuid,
                    project_id=test_project_id,
                    domain_name=test_domain_name,
                    resource_group=test_scaling_group,
                    period_start=period_start,
                    period_end=period_end,
                    resource_usage=ResourceSlot({"cpu": Decimal("300")}),
                )
            )

        bulk_creator = BulkCreator(specs=specs)
        results = await resource_usage_history_repository.bulk_create_kernel_usage_records(
            bulk_creator
        )

        assert len(results) == 5
        for result in results:
            assert result.resource_group == test_scaling_group
            assert result.domain_name == test_domain_name

    @pytest.mark.asyncio
    async def test_search_kernel_usage_records(
        self,
        resource_usage_history_repository: ResourceUsageHistoryRepository,
        test_scaling_group: str,
        test_domain_name: str,
        test_project_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
    ) -> None:
        """Test searching kernel usage records with BatchQuerier"""
        kernel_id = uuid.uuid4()
        session_id = uuid.uuid4()
        now = datetime.now(tz=UTC)

        # Create multiple records for same kernel
        specs = []
        for i in range(3):
            period_start = now - timedelta(minutes=5 * (i + 1))
            period_end = now - timedelta(minutes=5 * i)
            specs.append(
                KernelUsageRecordCreatorSpec(
                    kernel_id=kernel_id,
                    session_id=session_id,
                    user_uuid=test_user_uuid,
                    project_id=test_project_id,
                    domain_name=test_domain_name,
                    resource_group=test_scaling_group,
                    period_start=period_start,
                    period_end=period_end,
                    resource_usage=ResourceSlot({"cpu": Decimal("300")}),
                )
            )

        bulk_creator = BulkCreator(specs=specs)
        await resource_usage_history_repository.bulk_create_kernel_usage_records(bulk_creator)

        # Search by kernel using BatchQuerier
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[KernelUsageRecordConditions.by_kernel_id(kernel_id)],
            orders=[KernelUsageRecordOrders.by_period_start()],
        )
        result = await resource_usage_history_repository.search_kernel_usage_records(querier)

        assert result.total_count == 3
        assert len(result.items) == 3
        for item in result.items:
            assert item.kernel_id == kernel_id

    # ==================== Domain Usage Bucket Tests ====================

    @pytest.mark.asyncio
    async def test_create_domain_usage_bucket(
        self,
        resource_usage_history_repository: ResourceUsageHistoryRepository,
        test_scaling_group: str,
        test_domain_name: str,
    ) -> None:
        """Test creating domain usage bucket"""
        today = datetime.now(tz=UTC).date()

        creator = Creator(
            spec=DomainUsageBucketCreatorSpec(
                domain_name=test_domain_name,
                resource_group=test_scaling_group,
                period_start=today,
                period_end=today + timedelta(days=1),
                decay_unit_days=1,
                resource_usage=ResourceSlot({
                    "cpu": Decimal("86400"),
                    "mem": Decimal("86400000000"),
                }),
                capacity_snapshot=ResourceSlot({
                    "cpu": Decimal("16"),
                    "mem": Decimal("68719476736"),
                }),
            )
        )

        result = await resource_usage_history_repository.create_domain_usage_bucket(creator)

        assert result.domain_name == test_domain_name
        assert result.resource_group == test_scaling_group
        assert result.period_start == today
        assert result.resource_usage["cpu"] == Decimal("86400")

    @pytest.mark.asyncio
    async def test_upsert_domain_usage_bucket_insert(
        self,
        resource_usage_history_repository: ResourceUsageHistoryRepository,
        test_scaling_group: str,
        test_domain_name: str,
    ) -> None:
        """Test upsert domain usage bucket - insert case"""
        today = datetime.now(tz=UTC).date()

        upserter = Upserter(
            spec=DomainUsageBucketUpserterSpec(
                domain_name=test_domain_name,
                resource_group=test_scaling_group,
                period_start=today,
                period_end=today + timedelta(days=1),
                decay_unit_days=1,
                resource_usage=ResourceSlot({"cpu": Decimal("3600")}),
                capacity_snapshot=ResourceSlot({"cpu": Decimal("8")}),
            )
        )

        result = await resource_usage_history_repository.upsert_domain_usage_bucket(upserter)

        assert result.domain_name == test_domain_name
        assert result.resource_usage["cpu"] == Decimal("3600")

    @pytest.mark.asyncio
    async def test_upsert_domain_usage_bucket_update(
        self,
        resource_usage_history_repository: ResourceUsageHistoryRepository,
        test_scaling_group: str,
        test_domain_name: str,
    ) -> None:
        """Test upsert domain usage bucket - update case"""
        today = datetime.now(tz=UTC).date()

        # First upsert (insert)
        upserter1 = Upserter(
            spec=DomainUsageBucketUpserterSpec(
                domain_name=test_domain_name,
                resource_group=test_scaling_group,
                period_start=today,
                period_end=today + timedelta(days=1),
                decay_unit_days=1,
                resource_usage=ResourceSlot({"cpu": Decimal("3600")}),
                capacity_snapshot=ResourceSlot({"cpu": Decimal("8")}),
            )
        )
        await resource_usage_history_repository.upsert_domain_usage_bucket(upserter1)

        # Second upsert (update)
        upserter2 = Upserter(
            spec=DomainUsageBucketUpserterSpec(
                domain_name=test_domain_name,
                resource_group=test_scaling_group,
                period_start=today,
                period_end=today + timedelta(days=1),
                decay_unit_days=1,
                resource_usage=ResourceSlot({"cpu": Decimal("7200")}),
                capacity_snapshot=ResourceSlot({"cpu": Decimal("8")}),
            )
        )
        result = await resource_usage_history_repository.upsert_domain_usage_bucket(upserter2)

        assert result.resource_usage["cpu"] == Decimal("7200")

    @pytest.mark.asyncio
    async def test_search_domain_usage_buckets(
        self,
        resource_usage_history_repository: ResourceUsageHistoryRepository,
        test_scaling_group: str,
        test_domain_name: str,
    ) -> None:
        """Test searching domain usage buckets with BatchQuerier"""
        today = datetime.now(tz=UTC).date()

        # Create buckets for multiple days
        for i in range(5):
            bucket_date = today - timedelta(days=i)
            creator = Creator(
                spec=DomainUsageBucketCreatorSpec(
                    domain_name=test_domain_name,
                    resource_group=test_scaling_group,
                    period_start=bucket_date,
                    period_end=bucket_date + timedelta(days=1),
                    decay_unit_days=1,
                    resource_usage=ResourceSlot({"cpu": Decimal("3600")}),
                    capacity_snapshot=ResourceSlot({"cpu": Decimal("8")}),
                )
            )
            await resource_usage_history_repository.create_domain_usage_bucket(creator)

        # Search with lookback window using BatchQuerier
        lookback_start = today - timedelta(days=3)
        lookback_end = today
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[
                DomainUsageBucketConditions.by_resource_group(test_scaling_group),
                DomainUsageBucketConditions.by_period_range(lookback_start, lookback_end),
            ],
            orders=[DomainUsageBucketOrders.by_period_start()],
        )
        result = await resource_usage_history_repository.search_domain_usage_buckets(querier)

        assert result.total_count == 4  # days 0, 1, 2, 3
        assert len(result.items) == 4

    # ==================== User Usage Bucket Tests ====================

    @pytest.mark.asyncio
    async def test_create_user_usage_bucket(
        self,
        resource_usage_history_repository: ResourceUsageHistoryRepository,
        test_scaling_group: str,
        test_domain_name: str,
        test_project_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
    ) -> None:
        """Test creating user usage bucket"""
        today = datetime.now(tz=UTC).date()

        creator = Creator(
            spec=UserUsageBucketCreatorSpec(
                user_uuid=test_user_uuid,
                project_id=test_project_id,
                domain_name=test_domain_name,
                resource_group=test_scaling_group,
                period_start=today,
                period_end=today + timedelta(days=1),
                decay_unit_days=1,
                resource_usage=ResourceSlot({"cpu": Decimal("3600")}),
                capacity_snapshot=ResourceSlot({"cpu": Decimal("8")}),
            )
        )

        result = await resource_usage_history_repository.create_user_usage_bucket(creator)

        assert result.user_uuid == test_user_uuid
        assert result.project_id == test_project_id
        assert result.resource_usage["cpu"] == Decimal("3600")

    @pytest.mark.asyncio
    async def test_upsert_user_usage_bucket(
        self,
        resource_usage_history_repository: ResourceUsageHistoryRepository,
        test_scaling_group: str,
        test_domain_name: str,
        test_project_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
    ) -> None:
        """Test upsert user usage bucket"""
        today = datetime.now(tz=UTC).date()

        upserter = Upserter(
            spec=UserUsageBucketUpserterSpec(
                user_uuid=test_user_uuid,
                project_id=test_project_id,
                domain_name=test_domain_name,
                resource_group=test_scaling_group,
                period_start=today,
                period_end=today + timedelta(days=1),
                decay_unit_days=1,
                resource_usage=ResourceSlot({"cpu": Decimal("7200")}),
                capacity_snapshot=ResourceSlot({"cpu": Decimal("8")}),
            )
        )

        result = await resource_usage_history_repository.upsert_user_usage_bucket(upserter)

        assert result.user_uuid == test_user_uuid
        assert result.resource_usage["cpu"] == Decimal("7200")

    # ==================== Project Usage Bucket Tests ====================

    @pytest.mark.asyncio
    async def test_create_project_usage_bucket(
        self,
        resource_usage_history_repository: ResourceUsageHistoryRepository,
        test_scaling_group: str,
        test_domain_name: str,
        test_project_id: uuid.UUID,
    ) -> None:
        """Test creating project usage bucket"""
        today = datetime.now(tz=UTC).date()

        creator = Creator(
            spec=ProjectUsageBucketCreatorSpec(
                project_id=test_project_id,
                domain_name=test_domain_name,
                resource_group=test_scaling_group,
                period_start=today,
                period_end=today + timedelta(days=1),
                decay_unit_days=1,
                resource_usage=ResourceSlot({"cpu": Decimal("3600")}),
                capacity_snapshot=ResourceSlot({"cpu": Decimal("8")}),
            )
        )

        result = await resource_usage_history_repository.create_project_usage_bucket(creator)

        assert result.project_id == test_project_id
        assert result.resource_usage["cpu"] == Decimal("3600")

    # ==================== Aggregation Tests ====================

    @pytest.mark.asyncio
    async def test_get_aggregated_usage_by_user(
        self,
        resource_usage_history_repository: ResourceUsageHistoryRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group: str,
        test_domain_name: str,
        test_project_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
    ) -> None:
        """Test getting aggregated usage by user"""
        today = datetime.now(tz=UTC).date()

        # Create multiple user usage buckets with normalized entries
        for i in range(3):
            bucket_date = today - timedelta(days=i)
            creator = Creator(
                spec=UserUsageBucketCreatorSpec(
                    user_uuid=test_user_uuid,
                    project_id=test_project_id,
                    domain_name=test_domain_name,
                    resource_group=test_scaling_group,
                    period_start=bucket_date,
                    period_end=bucket_date + timedelta(days=1),
                    decay_unit_days=1,
                    resource_usage=ResourceSlot({"cpu": Decimal("3600")}),
                    capacity_snapshot=ResourceSlot({"cpu": Decimal("8")}),
                )
            )
            result = await resource_usage_history_repository.create_user_usage_bucket(creator)
            # Create normalized entries for aggregation queries
            async with db_with_cleanup.begin_session() as db_sess:
                db_sess.add(
                    UsageBucketEntryRow(
                        bucket_id=result.id,
                        bucket_type="user",
                        slot_name="cpu",
                        amount=Decimal("3600"),
                        duration_seconds=300,
                        capacity=Decimal("0"),
                    )
                )

        # Get aggregated usage
        lookback_start = today - timedelta(days=7)
        lookback_end = today
        results = await resource_usage_history_repository.get_aggregated_usage_by_user(
            resource_group=test_scaling_group,
            lookback_start=lookback_start,
            lookback_end=lookback_end,
        )

        key = (test_user_uuid, test_project_id)
        assert key in results
        assert results[key]["cpu"] == Decimal("10800")  # 3600 * 3

    @pytest.mark.asyncio
    async def test_get_aggregated_usage_by_user_empty(
        self,
        resource_usage_history_repository: ResourceUsageHistoryRepository,
        test_scaling_group: str,
    ) -> None:
        """Test getting aggregated usage with no data returns empty dict"""
        today = datetime.now(tz=UTC).date()
        lookback_start = today - timedelta(days=7)
        lookback_end = today

        results = await resource_usage_history_repository.get_aggregated_usage_by_user(
            resource_group=test_scaling_group,
            lookback_start=lookback_start,
            lookback_end=lookback_end,
        )

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_get_aggregated_usage_by_project(
        self,
        resource_usage_history_repository: ResourceUsageHistoryRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group: str,
        test_domain_name: str,
        test_project_id: uuid.UUID,
    ) -> None:
        """Test getting aggregated usage by project"""
        today = datetime.now(tz=UTC).date()

        # Create multiple project usage buckets
        for i in range(2):
            bucket_date = today - timedelta(days=i)
            creator = Creator(
                spec=ProjectUsageBucketCreatorSpec(
                    project_id=test_project_id,
                    domain_name=test_domain_name,
                    resource_group=test_scaling_group,
                    period_start=bucket_date,
                    period_end=bucket_date + timedelta(days=1),
                    decay_unit_days=1,
                    resource_usage=ResourceSlot({"cpu": Decimal("7200")}),
                    capacity_snapshot=ResourceSlot({"cpu": Decimal("8")}),
                )
            )
            result = await resource_usage_history_repository.create_project_usage_bucket(creator)
            # Create normalized entries for aggregation queries
            async with db_with_cleanup.begin_session() as db_sess:
                db_sess.add(
                    UsageBucketEntryRow(
                        bucket_id=result.id,
                        bucket_type="project",
                        slot_name="cpu",
                        amount=Decimal("7200"),
                        duration_seconds=300,
                        capacity=Decimal("0"),
                    )
                )

        # Get aggregated usage
        lookback_start = today - timedelta(days=7)
        lookback_end = today
        results = await resource_usage_history_repository.get_aggregated_usage_by_project(
            resource_group=test_scaling_group,
            lookback_start=lookback_start,
            lookback_end=lookback_end,
        )

        assert test_project_id in results
        assert results[test_project_id]["cpu"] == Decimal("14400")  # 7200 * 2

    @pytest.mark.asyncio
    async def test_get_aggregated_usage_by_domain(
        self,
        resource_usage_history_repository: ResourceUsageHistoryRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group: str,
        test_domain_name: str,
    ) -> None:
        """Test getting aggregated usage by domain"""
        today = datetime.now(tz=UTC).date()

        # Create multiple domain usage buckets
        for i in range(2):
            bucket_date = today - timedelta(days=i)
            creator = Creator(
                spec=DomainUsageBucketCreatorSpec(
                    domain_name=test_domain_name,
                    resource_group=test_scaling_group,
                    period_start=bucket_date,
                    period_end=bucket_date + timedelta(days=1),
                    decay_unit_days=1,
                    resource_usage=ResourceSlot({"cpu": Decimal("86400")}),
                    capacity_snapshot=ResourceSlot({"cpu": Decimal("16")}),
                )
            )
            result = await resource_usage_history_repository.create_domain_usage_bucket(creator)
            # Create normalized entries for aggregation queries
            async with db_with_cleanup.begin_session() as db_sess:
                db_sess.add(
                    UsageBucketEntryRow(
                        bucket_id=result.id,
                        bucket_type="domain",
                        slot_name="cpu",
                        amount=Decimal("86400"),
                        duration_seconds=300,
                        capacity=Decimal("0"),
                    )
                )

        # Get aggregated usage
        lookback_start = today - timedelta(days=7)
        lookback_end = today
        results = await resource_usage_history_repository.get_aggregated_usage_by_domain(
            resource_group=test_scaling_group,
            lookback_start=lookback_start,
            lookback_end=lookback_end,
        )

        assert test_domain_name in results
        assert results[test_domain_name]["cpu"] == Decimal("172800")  # 86400 * 2
