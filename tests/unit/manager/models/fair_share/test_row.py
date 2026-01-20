"""Tests for Fair Share Row models."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.fair_share import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class TestDomainFairShareRow:
    """Tests for DomainFairShareRow model."""

    async def test_create_with_defaults(
        self,
        database_with_fair_share_tables: ExtendedAsyncSAEngine,
        domain_fair_share_id: uuid.UUID,
    ) -> None:
        """Verify default values are set correctly."""
        async with database_with_fair_share_tables.begin_readonly_session() as db_sess:
            row = await db_sess.get(DomainFairShareRow, domain_fair_share_id)
            assert row is not None
            assert row.weight == Decimal("1.0")
            assert row.fair_share_factor == Decimal("1.0")
            assert row.normalized_usage == Decimal("0")

    async def test_create_with_usage_values(
        self,
        database_with_fair_share_tables: ExtendedAsyncSAEngine,
        domain_fair_share_with_usage_id: uuid.UUID,
    ) -> None:
        """Verify calculated fields are stored correctly."""
        async with database_with_fair_share_tables.begin_readonly_session() as db_sess:
            row = await db_sess.get(DomainFairShareRow, domain_fair_share_with_usage_id)
            assert row is not None
            assert row.weight == Decimal("2.0")
            assert row.total_decayed_usage["cpu"] == Decimal("3600")
            assert row.normalized_usage == Decimal("0.15")
            assert row.fair_share_factor == Decimal("0.945742")

    async def test_unique_constraint_violation(
        self,
        database_with_fair_share_tables: ExtendedAsyncSAEngine,
        domain_fair_share_id: uuid.UUID,
        domain_name: str,
        scaling_group: str,
    ) -> None:
        """Duplicate (scaling_group, domain_name) should raise IntegrityError."""
        duplicate = DomainFairShareRow(
            domain_name=domain_name,
            resource_group=scaling_group,
            weight=Decimal("1.0"),
            total_decayed_usage=ResourceSlot(),
            normalized_usage=Decimal("0"),
            fair_share_factor=Decimal("1.0"),
            resource_weights=ResourceSlot(),
        )
        with pytest.raises(IntegrityError):
            async with database_with_fair_share_tables.begin_session() as db_sess:
                db_sess.add(duplicate)
                await db_sess.flush()

    async def test_decimal_precision_weight(
        self,
        database_with_fair_share_tables: ExtendedAsyncSAEngine,
        domain_name: str,
        scaling_group: str,
    ) -> None:
        """Weight field should preserve Numeric(10, 4) precision."""
        row = DomainFairShareRow(
            domain_name=domain_name,
            resource_group=scaling_group,
            weight=Decimal("1234.5678"),
            total_decayed_usage=ResourceSlot(),
            normalized_usage=Decimal("0"),
            fair_share_factor=Decimal("1.0"),
            resource_weights=ResourceSlot(),
        )
        async with database_with_fair_share_tables.begin_session() as db_sess:
            db_sess.add(row)
            await db_sess.flush()
            row_id = row.id

        async with database_with_fair_share_tables.begin_readonly_session() as db_sess:
            saved = await db_sess.get(DomainFairShareRow, row_id)
            assert saved is not None
            assert saved.weight == Decimal("1234.5678")


class TestProjectFairShareRow:
    """Tests for ProjectFairShareRow model."""

    async def test_create_with_defaults(
        self,
        database_with_fair_share_tables: ExtendedAsyncSAEngine,
        project_fair_share_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> None:
        """Verify project fair share is created with correct project_id."""
        async with database_with_fair_share_tables.begin_readonly_session() as db_sess:
            row = await db_sess.get(ProjectFairShareRow, project_fair_share_id)
            assert row is not None
            assert row.project_id == project_id
            assert row.weight == Decimal("1.0")

    async def test_unique_constraint_violation(
        self,
        database_with_fair_share_tables: ExtendedAsyncSAEngine,
        project_fair_share_id: uuid.UUID,
        project_id: uuid.UUID,
        domain_name: str,
        scaling_group: str,
    ) -> None:
        """Duplicate (scaling_group, project_id) should raise IntegrityError."""
        duplicate = ProjectFairShareRow(
            project_id=project_id,
            domain_name=domain_name,
            resource_group=scaling_group,
            weight=Decimal("1.0"),
            total_decayed_usage=ResourceSlot(),
            normalized_usage=Decimal("0"),
            fair_share_factor=Decimal("1.0"),
            resource_weights=ResourceSlot(),
        )
        with pytest.raises(IntegrityError):
            async with database_with_fair_share_tables.begin_session() as db_sess:
                db_sess.add(duplicate)
                await db_sess.flush()


class TestUserFairShareRow:
    """Tests for UserFairShareRow model."""

    async def test_create_with_defaults(
        self,
        database_with_fair_share_tables: ExtendedAsyncSAEngine,
        user_fair_share_id: uuid.UUID,
        user_uuid: uuid.UUID,
        project_id: uuid.UUID,
    ) -> None:
        """Verify user fair share is created with correct user_uuid and project_id."""
        async with database_with_fair_share_tables.begin_readonly_session() as db_sess:
            row = await db_sess.get(UserFairShareRow, user_fair_share_id)
            assert row is not None
            assert row.user_uuid == user_uuid
            assert row.project_id == project_id
            assert row.weight == Decimal("1.0")

    async def test_unique_constraint_violation(
        self,
        database_with_fair_share_tables: ExtendedAsyncSAEngine,
        user_fair_share_id: uuid.UUID,
        user_uuid: uuid.UUID,
        project_id: uuid.UUID,
        domain_name: str,
        scaling_group: str,
    ) -> None:
        """Duplicate (scaling_group, user_uuid, project_id) should raise IntegrityError."""
        duplicate = UserFairShareRow(
            user_uuid=user_uuid,
            project_id=project_id,
            domain_name=domain_name,
            resource_group=scaling_group,
            weight=Decimal("1.0"),
            total_decayed_usage=ResourceSlot(),
            normalized_usage=Decimal("0"),
            fair_share_factor=Decimal("1.0"),
            resource_weights=ResourceSlot(),
        )
        with pytest.raises(IntegrityError):
            async with database_with_fair_share_tables.begin_session() as db_sess:
                db_sess.add(duplicate)
                await db_sess.flush()

    async def test_large_resource_seconds_values(
        self,
        database_with_fair_share_tables: ExtendedAsyncSAEngine,
        user_fair_share_with_large_usage_id: uuid.UUID,
    ) -> None:
        """Verify large resource-seconds values are stored correctly."""
        async with database_with_fair_share_tables.begin_readonly_session() as db_sess:
            row = await db_sess.get(UserFairShareRow, user_fair_share_with_large_usage_id)
            assert row is not None
            # 8 GPUs × 28 days × 86400 sec/day = 19,353,600 GPU-seconds
            assert row.total_decayed_usage["cuda.device"] == Decimal("19353600")
            assert row.normalized_usage == Decimal("0.186")
