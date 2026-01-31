"""Tests for export adapter with dynamic JOIN support."""

from __future__ import annotations

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.api.export.adapter import ExportAdapter
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.repositories.base.export import (
    ExportFieldDef,
    ExportFieldType,
    JoinDef,
    ReportDef,
)

# =============================================================================
# Test Models
# =============================================================================


class ParentRow(Base):
    """Parent model for testing."""

    __tablename__ = "test_parent"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(GUID, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    policy_name: Mapped[str] = mapped_column(sa.String(50), nullable=True)


class PolicyRow(Base):
    """Policy model for N:1 JOIN testing."""

    __tablename__ = "test_policy"
    __table_args__ = {"extend_existing": True}

    name: Mapped[str] = mapped_column(sa.String(50), primary_key=True)
    max_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=10)


class ChildAssocRow(Base):
    """Association model for 1:N JOIN testing."""

    __tablename__ = "test_child_assoc"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(GUID, primary_key=True)
    parent_id: Mapped[str] = mapped_column(GUID, nullable=False)
    child_id: Mapped[str] = mapped_column(GUID, nullable=False)


class ChildRow(Base):
    """Child model for 1:N JOIN testing."""

    __tablename__ = "test_child"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(GUID, primary_key=True)
    child_name: Mapped[str] = mapped_column(sa.String(50), nullable=False)


# =============================================================================
# Join Definitions
# =============================================================================

POLICY_JOIN = JoinDef(
    table=PolicyRow.__table__,
    condition=ParentRow.policy_name == PolicyRow.name,
)

CHILD_ASSOC_JOIN = JoinDef(
    table=ChildAssocRow.__table__,
    condition=ParentRow.id == ChildAssocRow.parent_id,
)

CHILD_JOIN = JoinDef(
    table=ChildRow.__table__,
    condition=ChildAssocRow.child_id == ChildRow.id,
)

CHILD_JOINS = (CHILD_ASSOC_JOIN, CHILD_JOIN)


# =============================================================================
# Test Fixtures
# =============================================================================


class TestCollectJoins:
    """Tests for _collect_joins method."""

    @pytest.fixture
    def adapter(self) -> ExportAdapter:
        """Create ExportAdapter instance."""
        return ExportAdapter()

    @pytest.fixture
    def field_without_joins(self) -> ExportFieldDef:
        """Field definition without any joins."""
        return ExportFieldDef(
            key="id",
            name="ID",
            description="Parent ID",
            field_type=ExportFieldType.UUID,
            column=ParentRow.id,
        )

    @pytest.fixture
    def field_with_name(self) -> ExportFieldDef:
        """Field definition for name without joins."""
        return ExportFieldDef(
            key="name",
            name="Name",
            description="Parent name",
            field_type=ExportFieldType.STRING,
            column=ParentRow.name,
        )

    @pytest.fixture
    def field_with_single_join(self) -> ExportFieldDef:
        """Field definition with single join (N:1)."""
        return ExportFieldDef(
            key="policy_max_count",
            name="Policy Max Count",
            description="Policy max count",
            field_type=ExportFieldType.INTEGER,
            column=PolicyRow.max_count,
            joins=frozenset({POLICY_JOIN}),
        )

    @pytest.fixture
    def field_with_multiple_joins(self) -> ExportFieldDef:
        """Field definition with multiple joins (1:N)."""
        return ExportFieldDef(
            key="child_name",
            name="Child Name",
            description="Child name",
            field_type=ExportFieldType.STRING,
            column=ChildRow.child_name,
            joins=CHILD_JOINS,
        )

    @pytest.fixture
    def another_field_with_same_joins(self) -> ExportFieldDef:
        """Another field with the same multiple joins."""
        return ExportFieldDef(
            key="child_id",
            name="Child ID",
            description="Child ID",
            field_type=ExportFieldType.UUID,
            column=ChildRow.id,
            joins=CHILD_JOINS,
        )

    def test_returns_empty_for_fields_without_joins(
        self,
        adapter: ExportAdapter,
        field_without_joins: ExportFieldDef,
        field_with_name: ExportFieldDef,
    ) -> None:
        """Fields without joins should return empty list."""
        fields = [field_without_joins, field_with_name]

        result = adapter._collect_joins(fields)

        assert result == []

    def test_returns_single_join(
        self,
        adapter: ExportAdapter,
        field_without_joins: ExportFieldDef,
        field_with_single_join: ExportFieldDef,
    ) -> None:
        """Field with single join should return that join."""
        fields = [field_without_joins, field_with_single_join]

        result = adapter._collect_joins(fields)

        assert len(result) == 1
        assert POLICY_JOIN in result

    def test_returns_multiple_joins_from_single_field(
        self,
        adapter: ExportAdapter,
        field_without_joins: ExportFieldDef,
        field_with_multiple_joins: ExportFieldDef,
    ) -> None:
        """Field with multiple joins should return all joins."""
        fields = [field_without_joins, field_with_multiple_joins]

        result = adapter._collect_joins(fields)

        assert len(result) == 2
        assert CHILD_ASSOC_JOIN in result
        assert CHILD_JOIN in result

    def test_deduplicates_joins_from_multiple_fields(
        self,
        adapter: ExportAdapter,
        field_with_multiple_joins: ExportFieldDef,
        another_field_with_same_joins: ExportFieldDef,
    ) -> None:
        """Same joins from multiple fields should be deduplicated."""
        fields = [field_with_multiple_joins, another_field_with_same_joins]

        result = adapter._collect_joins(fields)

        assert len(result) == 2
        assert CHILD_ASSOC_JOIN in result
        assert CHILD_JOIN in result

    def test_collects_all_unique_joins(
        self,
        adapter: ExportAdapter,
        field_without_joins: ExportFieldDef,
        field_with_single_join: ExportFieldDef,
        field_with_multiple_joins: ExportFieldDef,
    ) -> None:
        """All unique joins should be collected."""
        fields = [field_without_joins, field_with_single_join, field_with_multiple_joins]

        result = adapter._collect_joins(fields)

        assert len(result) == 3
        assert POLICY_JOIN in result
        assert CHILD_ASSOC_JOIN in result
        assert CHILD_JOIN in result


class TestBuildSelectFromWithJoins:
    """Tests for _build_select_from_with_joins method."""

    @pytest.fixture
    def adapter(self) -> ExportAdapter:
        """Create ExportAdapter instance."""
        return ExportAdapter()

    @pytest.fixture
    def base_table(self) -> sa.FromClause:
        """Base table for testing."""
        return ParentRow.__table__

    def test_returns_base_table_for_empty_joins(
        self,
        adapter: ExportAdapter,
        base_table: sa.FromClause,
    ) -> None:
        """Empty joins should return base table unchanged."""
        result = adapter._build_select_from_with_joins(base_table, [])

        assert result is base_table

    def test_applies_single_join(
        self,
        adapter: ExportAdapter,
        base_table: sa.FromClause,
    ) -> None:
        """Single join should be applied to base table."""
        joins = [POLICY_JOIN]

        result = adapter._build_select_from_with_joins(base_table, joins)

        # Verify it's a Join object
        assert isinstance(result, sa.sql.selectable.Join)
        # Verify the joined table is policy table
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "test_policy" in compiled
        assert "LEFT OUTER JOIN" in compiled

    def test_applies_multiple_joins_in_order(
        self,
        adapter: ExportAdapter,
        base_table: sa.FromClause,
    ) -> None:
        """Multiple joins should be applied in order."""
        joins = [CHILD_ASSOC_JOIN, CHILD_JOIN]

        result = adapter._build_select_from_with_joins(base_table, joins)

        # Verify it's a Join object
        assert isinstance(result, sa.sql.selectable.Join)
        # Verify both tables are joined
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "test_child_assoc" in compiled
        assert "test_child" in compiled

    def test_applies_all_joins(
        self,
        adapter: ExportAdapter,
        base_table: sa.FromClause,
    ) -> None:
        """All joins should be applied."""
        joins = [POLICY_JOIN, CHILD_ASSOC_JOIN, CHILD_JOIN]

        result = adapter._build_select_from_with_joins(base_table, joins)

        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "test_policy" in compiled
        assert "test_child_assoc" in compiled
        assert "test_child" in compiled


class TestBuildProjectQueryWithJoins:
    """Tests for build_project_query with dynamic JOINs."""

    @pytest.fixture
    def adapter(self) -> ExportAdapter:
        """Create ExportAdapter instance."""
        return ExportAdapter()

    @pytest.fixture
    def basic_fields(self) -> list[ExportFieldDef]:
        """Basic fields without joins."""
        return [
            ExportFieldDef(
                key="id",
                name="ID",
                description="Parent ID",
                field_type=ExportFieldType.UUID,
                column=ParentRow.id,
            ),
            ExportFieldDef(
                key="name",
                name="Name",
                description="Parent name",
                field_type=ExportFieldType.STRING,
                column=ParentRow.name,
            ),
        ]

    @pytest.fixture
    def policy_field(self) -> ExportFieldDef:
        """Field with policy join."""
        return ExportFieldDef(
            key="policy_max_count",
            name="Policy Max Count",
            description="Policy max count",
            field_type=ExportFieldType.INTEGER,
            column=PolicyRow.max_count,
            joins=frozenset({POLICY_JOIN}),
        )

    @pytest.fixture
    def child_field(self) -> ExportFieldDef:
        """Field with child joins."""
        return ExportFieldDef(
            key="child_name",
            name="Child Name",
            description="Child name",
            field_type=ExportFieldType.STRING,
            column=ChildRow.child_name,
            joins=CHILD_JOINS,
        )

    @pytest.fixture
    def report_without_joins(
        self,
        basic_fields: list[ExportFieldDef],
    ) -> ReportDef:
        """Report with only basic fields (no joins)."""
        return ReportDef(
            report_key="test-report",
            name="Test Report",
            description="Test report",
            select_from=ParentRow.__table__,
            fields=basic_fields,
        )

    @pytest.fixture
    def report_with_all_fields(
        self,
        basic_fields: list[ExportFieldDef],
        policy_field: ExportFieldDef,
        child_field: ExportFieldDef,
    ) -> ReportDef:
        """Report with all fields including joins."""
        return ReportDef(
            report_key="test-report",
            name="Test Report",
            description="Test report",
            select_from=ParentRow.__table__,
            fields=[*basic_fields, policy_field, child_field],
        )

    def test_no_joins_when_basic_fields_only(
        self,
        adapter: ExportAdapter,
        report_with_all_fields: ReportDef,
    ) -> None:
        """Selecting only basic fields should not add JOINs."""
        query = adapter.build_project_query(
            report=report_with_all_fields,
            fields=["id", "name"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        # Should be the base table, not a Join
        assert query.select_from is ParentRow.__table__

    def test_single_join_when_policy_field_selected(
        self,
        adapter: ExportAdapter,
        report_with_all_fields: ReportDef,
    ) -> None:
        """Selecting policy field should add single JOIN."""
        query = adapter.build_project_query(
            report=report_with_all_fields,
            fields=["id", "policy_max_count"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        assert "test_policy" in compiled
        assert "test_child" not in compiled

    def test_multiple_joins_when_child_field_selected(
        self,
        adapter: ExportAdapter,
        report_with_all_fields: ReportDef,
    ) -> None:
        """Selecting child field should add multiple JOINs."""
        query = adapter.build_project_query(
            report=report_with_all_fields,
            fields=["id", "child_name"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        assert "test_child_assoc" in compiled
        assert "test_child" in compiled

    def test_all_joins_when_all_join_fields_selected(
        self,
        adapter: ExportAdapter,
        report_with_all_fields: ReportDef,
    ) -> None:
        """Selecting all join fields should add all JOINs."""
        query = adapter.build_project_query(
            report=report_with_all_fields,
            fields=["id", "policy_max_count", "child_name"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        assert "test_policy" in compiled
        assert "test_child_assoc" in compiled
        assert "test_child" in compiled

    def test_all_fields_selected_when_none_specified(
        self,
        adapter: ExportAdapter,
        report_with_all_fields: ReportDef,
    ) -> None:
        """None for fields should select all fields with all JOINs."""
        query = adapter.build_project_query(
            report=report_with_all_fields,
            fields=None,
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        # All fields should be selected
        assert len(query.fields) == 4

        # All JOINs should be applied
        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        assert "test_policy" in compiled
        assert "test_child_assoc" in compiled
        assert "test_child" in compiled
