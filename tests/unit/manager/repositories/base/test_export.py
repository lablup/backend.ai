"""Unit tests for export types and functions."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.repositories.base.export import (
    ExportFieldDef,
    ExportFieldType,
    ReportDef,
    StreamingExportQuery,
    execute_streaming_export,
)
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


# =============================================================================
# Test Model
# =============================================================================


class ExportTestRow(Base):
    """ORM model for export testing."""

    __tablename__ = "test_export"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(GUID, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    value: Mapped[int] = mapped_column(sa.Integer, nullable=True)
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="active")


# Field definitions for test model
TEST_EXPORT_FIELDS: list[ExportFieldDef] = [
    ExportFieldDef(
        key="id",
        name="ID",
        description="Unique ID",
        field_type=ExportFieldType.UUID,
        column=ExportTestRow.id,
    ),
    ExportFieldDef(
        key="name",
        name="Name",
        description="Item name",
        field_type=ExportFieldType.STRING,
        column=ExportTestRow.name,
    ),
    ExportFieldDef(
        key="value",
        name="Value",
        description="Item value",
        field_type=ExportFieldType.INTEGER,
        column=ExportTestRow.value,
    ),
    ExportFieldDef(
        key="status",
        name="Status",
        description="Item status",
        field_type=ExportFieldType.STRING,
        column=ExportTestRow.status,
    ),
]


# =============================================================================
# Test Types
# =============================================================================


class TestExportFieldDef:
    """Tests for ExportFieldDef dataclass."""

    def test_formatter(self) -> None:
        """Test field definition with custom formatter."""
        formatter = lambda x: f"formatted-{x}"
        field = ExportFieldDef(
            key="status",
            name="Status",
            description="Status field",
            field_type=ExportFieldType.STRING,
            column=ExportTestRow.status,
            formatter=formatter,
        )
        assert field.formatter is not None
        assert field.formatter("test") == "formatted-test"


class TestReportDef:
    """Tests for ReportDef dataclass."""

    @pytest.fixture
    def sample_fields(self) -> list[ExportFieldDef]:
        """Create sample field definitions."""
        return [
            ExportFieldDef(
                key="id",
                name="ID",
                description="Unique ID",
                field_type=ExportFieldType.UUID,
                column=ExportTestRow.id,
            ),
            ExportFieldDef(
                key="name",
                name="Name",
                description="Item name",
                field_type=ExportFieldType.STRING,
                column=ExportTestRow.name,
            ),
            ExportFieldDef(
                key="value",
                name="Value",
                description="Item value",
                field_type=ExportFieldType.INTEGER,
                column=ExportTestRow.value,
            ),
        ]

    @pytest.fixture
    def sample_report(self, sample_fields: list[ExportFieldDef]) -> ReportDef:
        """Create sample report definition."""
        return ReportDef(
            report_key="test-report",
            name="Test Report",
            description="Test report for unit tests",
            fields=sample_fields,
        )

    def test_get_field(self, sample_report: ReportDef) -> None:
        """Test get_field method."""
        field = sample_report.get_field("name")
        assert field is not None
        assert field.key == "name"
        assert field.name == "Name"

        assert sample_report.get_field("nonexistent") is None

    def test_get_field_keys(self, sample_report: ReportDef) -> None:
        """Test get_field_keys method."""
        all_keys = sample_report.get_field_keys()
        assert all_keys == {"id", "name", "value"}

    def test_validate_field_keys(self, sample_report: ReportDef) -> None:
        """Test validate_field_keys method."""
        # Valid keys
        invalid = sample_report.validate_field_keys(["id", "name"])
        assert invalid == []

        # Mix of valid and invalid
        invalid = sample_report.validate_field_keys(["id", "invalid_key", "another_bad"])
        assert "invalid_key" in invalid
        assert "another_bad" in invalid
        assert "id" not in invalid


# =============================================================================
# Integration Tests for execute_streaming_export
# =============================================================================


class TestExecuteStreamingExport:
    """Integration tests for execute_streaming_export function."""

    @pytest.fixture
    async def db_with_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created."""
        async with with_tables(database_connection, [ExportTestRow]):
            yield database_connection

    @pytest.fixture
    async def sample_data(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[dict[str, str | int]], None]:
        """Insert sample data and return list of inserted data."""
        data: list[dict[str, str | int]] = [
            {
                "id": str(uuid4()),
                "name": f"item-{i}",
                "value": i * 100,
                "status": "active" if i % 2 == 0 else "inactive",
            }
            for i in range(1, 11)  # 10 rows
        ]

        async with db_with_tables.begin_session() as db_sess:
            await db_sess.execute(ExportTestRow.__table__.insert(), data)

        yield data

    @pytest.fixture
    def test_report(self) -> ReportDef:
        """Create test report definition."""
        return ReportDef(
            report_key="test-export",
            name="Test Export",
            description="Test export report",
            fields=TEST_EXPORT_FIELDS,
        )

    @pytest.mark.asyncio
    async def test_basic_streaming_export(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        sample_data: list[dict[str, str | int]],
        test_report: ReportDef,
    ) -> None:
        """Test basic streaming export functionality."""
        fields = test_report.get_fields_by_keys(["id", "name", "value"])

        query = StreamingExportQuery(
            fields=fields,
            conditions=[],
            orders=[],
            max_rows=100,
            statement_timeout_sec=60,
        )

        rows: list[Sequence[Any]] = []
        async for partition in execute_streaming_export(db_with_tables, query):
            for row_values in partition:
                rows.append(row_values)

        assert len(rows) == 10
        for row in rows:
            assert len(row) == 3  # id, name, value

    @pytest.mark.asyncio
    async def test_streaming_export_with_condition(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        sample_data: list[dict[str, str | int]],
        test_report: ReportDef,
    ) -> None:
        """Test streaming export with WHERE condition."""
        fields = test_report.get_fields_by_keys(["id", "name", "status"])

        query = StreamingExportQuery(
            fields=fields,
            conditions=[lambda: ExportTestRow.status == "active"],
            orders=[],
            max_rows=100,
            statement_timeout_sec=60,
        )

        rows: list[Sequence[Any]] = []
        async for partition in execute_streaming_export(db_with_tables, query):
            for row_values in partition:
                rows.append(row_values)

        # active: i % 2 == 0 → items 2, 4, 6, 8, 10 (5 rows)
        assert len(rows) == 5
        for row in rows:
            assert row[2] == "active"

    @pytest.mark.asyncio
    async def test_streaming_export_with_order(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        sample_data: list[dict[str, str | int]],
        test_report: ReportDef,
    ) -> None:
        """Test streaming export with ORDER BY."""
        fields = test_report.get_fields_by_keys(["name", "value"])

        query = StreamingExportQuery(
            fields=fields,
            conditions=[],
            orders=[ExportTestRow.value.desc()],
            max_rows=100,
            statement_timeout_sec=60,
        )

        rows: list[Sequence[Any]] = []
        async for partition in execute_streaming_export(db_with_tables, query):
            for row_values in partition:
                rows.append(row_values)

        assert len(rows) == 10
        # Verify descending order (value is at index 1)
        assert rows[0][1] == 1000
        assert rows[9][1] == 100

    @pytest.mark.asyncio
    async def test_streaming_export_max_rows_limit(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        sample_data: list[dict[str, str | int]],
        test_report: ReportDef,
    ) -> None:
        """Test that max_rows limit is applied."""
        fields = test_report.get_fields_by_keys(["id", "name"])

        query = StreamingExportQuery(
            fields=fields,
            conditions=[],
            orders=[],
            max_rows=3,
            statement_timeout_sec=60,
        )

        rows: list[Sequence[Any]] = []
        async for partition in execute_streaming_export(db_with_tables, query):
            for row_values in partition:
                rows.append(row_values)

        assert len(rows) == 3

    @pytest.mark.asyncio
    async def test_streaming_export_partition_size(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        sample_data: list[dict[str, str | int]],
        test_report: ReportDef,
    ) -> None:
        """Test that partition_size splits results into multiple partitions."""
        fields = test_report.get_fields_by_keys(["id", "name"])

        query = StreamingExportQuery(
            fields=fields,
            conditions=[],
            orders=[],
            max_rows=100,
            statement_timeout_sec=60,
        )

        # 10 rows with partition_size=3 → 4 partitions (3 + 3 + 3 + 1)
        partitions: list[Sequence[Sequence[Any]]] = []
        async for partition in execute_streaming_export(db_with_tables, query, partition_size=3):
            partitions.append(partition)

        assert len(partitions) == 4
        assert len(partitions[0]) == 3
        assert len(partitions[1]) == 3
        assert len(partitions[2]) == 3
        assert len(partitions[3]) == 1
