"""Tests for Resource Usage History Row models."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.resource_usage_history import (
    DomainUsageBucketRow,
    KernelUsageRecordRow,
    ProjectUsageBucketRow,
    UserUsageBucketRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class TestDomainUsageBucketRow:
    """Tests for DomainUsageBucketRow model."""

    async def test_create_with_defaults(
        self,
        database_with_usage_tables: ExtendedAsyncSAEngine,
        domain_usage_bucket_id: uuid.UUID,
    ) -> None:
        """Verify default values are set correctly."""
        async with database_with_usage_tables.begin_readonly_session() as db_sess:
            row = await db_sess.get(DomainUsageBucketRow, domain_usage_bucket_id)
            assert row is not None
            assert row.period_start == date(2024, 1, 1)
            assert row.decay_unit_days == 1
            assert row.resource_usage == ResourceSlot()
            assert row.capacity_snapshot == ResourceSlot()

    async def test_create_with_capacity_snapshot(
        self,
        database_with_usage_tables: ExtendedAsyncSAEngine,
        domain_usage_bucket_with_capacity_id: uuid.UUID,
    ) -> None:
        """Verify capacity snapshot values are stored correctly."""
        async with database_with_usage_tables.begin_readonly_session() as db_sess:
            row = await db_sess.get(DomainUsageBucketRow, domain_usage_bucket_with_capacity_id)
            assert row is not None
            assert row.resource_usage["cpu"] == Decimal("288000")
            assert row.capacity_snapshot["cpu"] == Decimal("8640000")
            assert row.capacity_snapshot["cuda.device"] == Decimal("691200")

    async def test_unique_constraint_violation(
        self,
        database_with_usage_tables: ExtendedAsyncSAEngine,
        domain_usage_bucket_id: uuid.UUID,
        domain_name: str,
        scaling_group: str,
    ) -> None:
        """Duplicate (domain_name, scaling_group, period_start) should raise IntegrityError."""
        duplicate = DomainUsageBucketRow(
            domain_name=domain_name,
            resource_group=scaling_group,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 1),
            decay_unit_days=1,
            resource_usage=ResourceSlot(),
            capacity_snapshot=ResourceSlot(),
        )
        with pytest.raises(IntegrityError):
            async with database_with_usage_tables.begin_session() as db_sess:
                db_sess.add(duplicate)
                await db_sess.flush()


class TestProjectUsageBucketRow:
    """Tests for ProjectUsageBucketRow model."""

    async def test_create_with_defaults(
        self,
        database_with_usage_tables: ExtendedAsyncSAEngine,
        project_usage_bucket_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> None:
        """Verify project usage bucket is created with correct project_id."""
        async with database_with_usage_tables.begin_readonly_session() as db_sess:
            row = await db_sess.get(ProjectUsageBucketRow, project_usage_bucket_id)
            assert row is not None
            assert row.project_id == project_id
            assert row.period_start == date(2024, 1, 1)

    async def test_unique_constraint_violation(
        self,
        database_with_usage_tables: ExtendedAsyncSAEngine,
        project_usage_bucket_id: uuid.UUID,
        project_id: uuid.UUID,
        domain_name: str,
        scaling_group: str,
    ) -> None:
        """Duplicate (project_id, scaling_group, period_start) should raise IntegrityError."""
        duplicate = ProjectUsageBucketRow(
            project_id=project_id,
            domain_name=domain_name,
            resource_group=scaling_group,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 1),
            decay_unit_days=1,
            resource_usage=ResourceSlot(),
            capacity_snapshot=ResourceSlot(),
        )
        with pytest.raises(IntegrityError):
            async with database_with_usage_tables.begin_session() as db_sess:
                db_sess.add(duplicate)
                await db_sess.flush()


class TestUserUsageBucketRow:
    """Tests for UserUsageBucketRow model."""

    async def test_create_with_defaults(
        self,
        database_with_usage_tables: ExtendedAsyncSAEngine,
        user_usage_bucket_id: uuid.UUID,
        user_uuid: uuid.UUID,
        project_id: uuid.UUID,
    ) -> None:
        """Verify user usage bucket is created with correct user_uuid and project_id."""
        async with database_with_usage_tables.begin_readonly_session() as db_sess:
            row = await db_sess.get(UserUsageBucketRow, user_usage_bucket_id)
            assert row is not None
            assert row.user_uuid == user_uuid
            assert row.project_id == project_id
            assert row.period_start == date(2024, 1, 1)

    async def test_unique_constraint_violation(
        self,
        database_with_usage_tables: ExtendedAsyncSAEngine,
        user_usage_bucket_id: uuid.UUID,
        user_uuid: uuid.UUID,
        project_id: uuid.UUID,
        domain_name: str,
        scaling_group: str,
    ) -> None:
        """Duplicate (user_uuid, project_id, scaling_group, period_start) should raise IntegrityError."""
        duplicate = UserUsageBucketRow(
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
        with pytest.raises(IntegrityError):
            async with database_with_usage_tables.begin_session() as db_sess:
                db_sess.add(duplicate)
                await db_sess.flush()


class TestKernelUsageRecordRow:
    """Tests for KernelUsageRecordRow model."""

    async def test_create_with_defaults(
        self,
        database_with_usage_tables: ExtendedAsyncSAEngine,
        kernel_usage_record_id: tuple[uuid.UUID, uuid.UUID, uuid.UUID],
    ) -> None:
        """Verify kernel usage record is created with correct IDs."""
        record_id, kernel_id, session_id = kernel_usage_record_id
        async with database_with_usage_tables.begin_readonly_session() as db_sess:
            row = await db_sess.get(KernelUsageRecordRow, record_id)
            assert row is not None
            assert row.kernel_id == kernel_id
            assert row.session_id == session_id
            assert row.resource_usage == ResourceSlot()

    async def test_create_with_resource_usage(
        self,
        database_with_usage_tables: ExtendedAsyncSAEngine,
        kernel_usage_record_with_usage_id: uuid.UUID,
    ) -> None:
        """Verify resource usage values (resource-seconds) are stored correctly."""
        async with database_with_usage_tables.begin_readonly_session() as db_sess:
            row = await db_sess.get(KernelUsageRecordRow, kernel_usage_record_with_usage_id)
            assert row is not None
            # 4 CPUs × 5 minutes = 1,200 CPU-seconds
            assert row.resource_usage["cpu"] == Decimal("1200")
            # 8 GiB × 5 minutes = 2,400 mem-seconds (in some unit)
            assert row.resource_usage["mem"] == Decimal("2400")
            # 2 GPUs × 5 minutes = 600 GPU-seconds
            assert row.resource_usage["cuda.device"] == Decimal("600")

    async def test_period_timestamps(
        self,
        database_with_usage_tables: ExtendedAsyncSAEngine,
        kernel_usage_record_with_usage_id: uuid.UUID,
    ) -> None:
        """Verify period timestamps are stored correctly."""
        async with database_with_usage_tables.begin_readonly_session() as db_sess:
            row = await db_sess.get(KernelUsageRecordRow, kernel_usage_record_with_usage_id)
            assert row is not None
            assert row.period_start is not None
            assert row.period_end is not None
            assert row.period_end > row.period_start
