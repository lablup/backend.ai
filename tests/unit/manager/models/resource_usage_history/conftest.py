from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_usage_history import (
    DomainUsageBucketRow,
    KernelUsageRecordRow,
    ProjectUsageBucketRow,
    UserUsageBucketRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables


@pytest.fixture
async def database_with_usage_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    """Set up tables required for resource usage history tests with automatic cleanup."""
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
            KeyPairRow,
            GroupRow,
            AgentRow,
            DomainUsageBucketRow,
            ProjectUsageBucketRow,
            UserUsageBucketRow,
            KernelUsageRecordRow,
        ],
    ):
        yield database_connection


@pytest.fixture
async def domain_name(
    database_with_usage_tables: ExtendedAsyncSAEngine,
) -> AsyncGenerator[str, None]:
    """Create DomainRow and return its name."""
    name = "test-domain"
    async with database_with_usage_tables.begin_session() as db_sess:
        db_sess.add(DomainRow(name=name))
    yield name


@pytest.fixture
async def scaling_group(
    database_with_usage_tables: ExtendedAsyncSAEngine,
) -> AsyncGenerator[str, None]:
    """Create ScalingGroupRow and return its name."""
    name = "default"
    async with database_with_usage_tables.begin_session() as db_sess:
        db_sess.add(
            ScalingGroupRow(
                name=name,
                description="Test scaling group",
                is_active=True,
                is_public=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
                use_host_network=False,
            )
        )
    yield name


@pytest.fixture
async def user_resource_policy(
    database_with_usage_tables: ExtendedAsyncSAEngine,
) -> AsyncGenerator[str, None]:
    """Create UserResourcePolicyRow and return its name."""
    name = "test-user-policy"
    async with database_with_usage_tables.begin_session() as db_sess:
        db_sess.add(
            UserResourcePolicyRow(
                name=name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
        )
    yield name


@pytest.fixture
async def project_resource_policy(
    database_with_usage_tables: ExtendedAsyncSAEngine,
) -> AsyncGenerator[str, None]:
    """Create ProjectResourcePolicyRow and return its name."""
    name = "test-project-policy"
    async with database_with_usage_tables.begin_session() as db_sess:
        db_sess.add(
            ProjectResourcePolicyRow(
                name=name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                max_network_count=5,
            )
        )
    yield name


@pytest.fixture
async def user_uuid(
    database_with_usage_tables: ExtendedAsyncSAEngine,
    domain_name: str,
    user_resource_policy: str,
) -> AsyncGenerator[uuid.UUID, None]:
    """Create UserRow and return its UUID."""
    user_id = uuid.uuid4()
    password_info = PasswordInfo(
        password="test_password",
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )
    async with database_with_usage_tables.begin_session() as db_sess:
        db_sess.add(
            UserRow(
                uuid=user_id,
                username="testuser",
                email="test@example.com",
                password=password_info,
                domain_name=domain_name,
                resource_policy=user_resource_policy,
            )
        )
    yield user_id


@pytest.fixture
async def project_id(
    database_with_usage_tables: ExtendedAsyncSAEngine,
    domain_name: str,
    project_resource_policy: str,
) -> AsyncGenerator[uuid.UUID, None]:
    """Create GroupRow and return its ID."""
    group_id = uuid.uuid4()
    async with database_with_usage_tables.begin_session() as db_sess:
        db_sess.add(
            GroupRow(
                id=group_id,
                name="test-project",
                domain_name=domain_name,
                resource_policy=project_resource_policy,
            )
        )
    yield group_id


@pytest.fixture
async def domain_usage_bucket_id(
    database_with_usage_tables: ExtendedAsyncSAEngine,
    domain_name: str,
    scaling_group: str,
) -> AsyncGenerator[uuid.UUID, None]:
    """Create DomainUsageBucketRow and return its ID."""
    row = DomainUsageBucketRow(
        domain_name=domain_name,
        resource_group=scaling_group,
        period_start=date(2024, 1, 1),
        period_end=date(2024, 1, 1),
        decay_unit_days=1,
        resource_usage=ResourceSlot(),
        capacity_snapshot=ResourceSlot(),
    )
    async with database_with_usage_tables.begin_session() as db_sess:
        db_sess.add(row)
        await db_sess.flush()
        row_id = row.id
    yield row_id


@pytest.fixture
async def domain_usage_bucket_with_capacity_id(
    database_with_usage_tables: ExtendedAsyncSAEngine,
    domain_name: str,
    scaling_group: str,
) -> AsyncGenerator[uuid.UUID, None]:
    """Create DomainUsageBucketRow with capacity snapshot and return its ID."""
    row = DomainUsageBucketRow(
        domain_name=domain_name,
        resource_group=scaling_group,
        period_start=date(2024, 1, 1),
        period_end=date(2024, 1, 1),
        decay_unit_days=1,
        resource_usage=ResourceSlot({
            "cpu": Decimal("288000"),
            "cuda.device": Decimal("57600"),
        }),
        capacity_snapshot=ResourceSlot({
            "cpu": Decimal("8640000"),
            "mem": Decimal("86400000"),
            "cuda.device": Decimal("691200"),
        }),
    )
    async with database_with_usage_tables.begin_session() as db_sess:
        db_sess.add(row)
        await db_sess.flush()
        row_id = row.id
    yield row_id


@pytest.fixture
async def project_usage_bucket_id(
    database_with_usage_tables: ExtendedAsyncSAEngine,
    project_id: uuid.UUID,
    domain_name: str,
    scaling_group: str,
) -> AsyncGenerator[uuid.UUID, None]:
    """Create ProjectUsageBucketRow and return its ID."""
    row = ProjectUsageBucketRow(
        project_id=project_id,
        domain_name=domain_name,
        resource_group=scaling_group,
        period_start=date(2024, 1, 1),
        period_end=date(2024, 1, 1),
        decay_unit_days=1,
        resource_usage=ResourceSlot(),
        capacity_snapshot=ResourceSlot(),
    )
    async with database_with_usage_tables.begin_session() as db_sess:
        db_sess.add(row)
        await db_sess.flush()
        row_id = row.id
    yield row_id


@pytest.fixture
async def user_usage_bucket_id(
    database_with_usage_tables: ExtendedAsyncSAEngine,
    user_uuid: uuid.UUID,
    project_id: uuid.UUID,
    domain_name: str,
    scaling_group: str,
) -> AsyncGenerator[uuid.UUID, None]:
    """Create UserUsageBucketRow and return its ID."""
    row = UserUsageBucketRow(
        user_uuid=user_uuid,
        project_id=project_id,
        domain_name=domain_name,
        resource_group=scaling_group,
        period_start=date(2024, 1, 1),
        period_end=date(2024, 1, 1),
        decay_unit_days=1,
        resource_usage=ResourceSlot(),
        capacity_snapshot=ResourceSlot(),
    )
    async with database_with_usage_tables.begin_session() as db_sess:
        db_sess.add(row)
        await db_sess.flush()
        row_id = row.id
    yield row_id


@pytest.fixture
async def kernel_usage_record_id(
    database_with_usage_tables: ExtendedAsyncSAEngine,
    user_uuid: uuid.UUID,
    project_id: uuid.UUID,
    domain_name: str,
    scaling_group: str,
) -> AsyncGenerator[tuple[uuid.UUID, uuid.UUID, uuid.UUID], None]:
    """Create KernelUsageRecordRow and return (record_id, kernel_id, session_id)."""
    kernel_id = uuid.uuid4()
    session_id = uuid.uuid4()
    now = datetime.now(UTC)

    row = KernelUsageRecordRow(
        kernel_id=kernel_id,
        session_id=session_id,
        user_uuid=user_uuid,
        project_id=project_id,
        domain_name=domain_name,
        resource_group=scaling_group,
        period_start=now,
        period_end=now,
        resource_usage=ResourceSlot(),
    )
    async with database_with_usage_tables.begin_session() as db_sess:
        db_sess.add(row)
        await db_sess.flush()
        row_id = row.id
    yield (row_id, kernel_id, session_id)


@pytest.fixture
async def kernel_usage_record_with_usage_id(
    database_with_usage_tables: ExtendedAsyncSAEngine,
    user_uuid: uuid.UUID,
    project_id: uuid.UUID,
    domain_name: str,
    scaling_group: str,
) -> AsyncGenerator[uuid.UUID, None]:
    """Create KernelUsageRecordRow with resource usage and return its ID."""
    row = KernelUsageRecordRow(
        kernel_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        user_uuid=user_uuid,
        project_id=project_id,
        domain_name=domain_name,
        resource_group=scaling_group,
        period_start=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        period_end=datetime(2024, 1, 1, 12, 5, 0, tzinfo=UTC),
        resource_usage=ResourceSlot({
            "cpu": Decimal("1200"),
            "mem": Decimal("2400"),
            "cuda.device": Decimal("600"),
        }),
    )
    async with database_with_usage_tables.begin_session() as db_sess:
        db_sess.add(row)
        await db_sess.flush()
        row_id = row.id
    yield row_id
