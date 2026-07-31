"""Tests for export adapter with dynamic JOIN support."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any, cast

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.export.request import (
    AuditLogExportFilter,
    SessionExportFilter,
    SessionExportUserNestedFilter,
)
from ai.backend.manager.api.rest.export.adapter import ExportAdapter
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.repositories.base.export import (
    ExportFieldDef,
    ExportFieldType,
    JoinDef,
    ReportDef,
    StreamingExportQuery,
)
from ai.backend.manager.repositories.export.reports.audit_log import AUDIT_LOG_REPORT
from ai.backend.manager.repositories.export.reports.session import SESSION_REPORT

# =============================================================================
# Test Models
# =============================================================================


class ParentRow(Base):  # type: ignore[misc]
    """Parent model for testing."""

    __tablename__ = "test_parent"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(GUID, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    policy_name: Mapped[str] = mapped_column(sa.String(50), nullable=True)


class PolicyRow(Base):  # type: ignore[misc]
    """Policy model for N:1 JOIN testing."""

    __tablename__ = "test_policy"
    __table_args__ = {"extend_existing": True}

    name: Mapped[str] = mapped_column(sa.String(50), primary_key=True)
    max_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=10)


class ChildAssocRow(Base):  # type: ignore[misc]
    """Association model for 1:N JOIN testing."""

    __tablename__ = "test_child_assoc"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(GUID, primary_key=True)
    parent_id: Mapped[str] = mapped_column(GUID, nullable=False)
    child_id: Mapped[str] = mapped_column(GUID, nullable=False)


class ChildRow(Base):  # type: ignore[misc]
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
        return cast(sa.FromClause, ParentRow.__table__)

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


class TestBuildSessionQueryUserFilter:
    """Tests for build_session_query nested user filtering (BA-6480).

    The session CSV export must support filtering by the owning user's email/username,
    which live on the users table. Filtering is expressed as a correlated EXISTS subquery
    over the users table, so users is never JOINed into the main FROM clause (no cartesian
    product) even when no user column is among the selected export fields.
    """

    @pytest.fixture
    def adapter(self) -> ExportAdapter:
        return ExportAdapter()

    @pytest.fixture
    def build_query(
        self,
        adapter: ExportAdapter,
    ) -> Callable[[list[str], SessionExportFilter], StreamingExportQuery]:
        """Build a session export query, holding the non-varying params constant."""

        def _build(fields: list[str], filter: SessionExportFilter) -> StreamingExportQuery:
            return adapter.build_session_query(
                report=SESSION_REPORT,
                fields=fields,
                filter=filter,
                order=None,
                max_rows=1000,
                statement_timeout_sec=60,
            )

        return _build

    @pytest.fixture
    def query_email_filter(
        self,
        build_query: Callable[[list[str], SessionExportFilter], StreamingExportQuery],
    ) -> StreamingExportQuery:
        """Filter by user.email; no user column selected."""
        return build_query(
            ["id", "name"],
            SessionExportFilter(
                user=SessionExportUserNestedFilter(email=StringFilter(equals="user@example.com"))
            ),
        )

    @pytest.fixture
    def query_email_and_username_filter(
        self,
        build_query: Callable[[list[str], SessionExportFilter], StreamingExportQuery],
    ) -> StreamingExportQuery:
        """Filter by both user.email and user.username; no user column selected."""
        return build_query(
            ["id", "name"],
            SessionExportFilter(
                user=SessionExportUserNestedFilter(
                    email=StringFilter(equals="user@example.com"),
                    username=StringFilter(contains="admin"),
                )
            ),
        )

    @pytest.fixture
    def query_no_filter(
        self,
        build_query: Callable[[list[str], SessionExportFilter], StreamingExportQuery],
    ) -> StreamingExportQuery:
        """No user filter and no user column selected."""
        return build_query(["id", "name"], SessionExportFilter())

    @pytest.fixture
    def query_user_column_selected(
        self,
        build_query: Callable[[list[str], SessionExportFilter], StreamingExportQuery],
    ) -> StreamingExportQuery:
        """Filter by user.email while also selecting the user_email output column."""
        return build_query(
            ["name", "status", "user_email"],
            SessionExportFilter(
                user=SessionExportUserNestedFilter(email=StringFilter(contains="admin@lablup.com"))
            ),
        )

    def test_user_email_filter_builds_exists_without_join(
        self,
        query_email_filter: StreamingExportQuery,
    ) -> None:
        """Filtering by user.email adds a correlated EXISTS subquery, not a users JOIN."""
        # No JOIN: the FROM clause stays the sessions table only.
        from_clause = str(
            query_email_filter.select_from.compile(compile_kwargs={"literal_binds": True})
        )
        assert "users" not in from_clause

        # A single correlated EXISTS condition over the users table.
        assert len(query_email_filter.conditions) == 1
        condition = str(
            query_email_filter.conditions[0]().compile(compile_kwargs={"literal_binds": True})
        )
        assert "EXISTS (SELECT" in condition
        assert "sessions.user_uuid = users.uuid" in condition
        assert "users.email" in condition

    def test_user_email_and_username_filters_share_single_exists(
        self,
        query_email_and_username_filter: StreamingExportQuery,
    ) -> None:
        """Both nested user filters combine (AND) inside a single EXISTS subquery."""
        from_clause = str(
            query_email_and_username_filter.select_from.compile(
                compile_kwargs={"literal_binds": True}
            )
        )
        assert "users" not in from_clause

        assert len(query_email_and_username_filter.conditions) == 1
        condition = str(
            query_email_and_username_filter.conditions[0]().compile(
                compile_kwargs={"literal_binds": True}
            )
        )
        assert "EXISTS (SELECT" in condition
        assert "users.email" in condition
        assert "users.username" in condition

    def test_no_user_condition_when_user_filter_absent(
        self,
        query_no_filter: StreamingExportQuery,
    ) -> None:
        """Without a user filter (and no user field selected), no users reference is added."""
        from_clause = str(
            query_no_filter.select_from.compile(compile_kwargs={"literal_binds": True})
        )
        assert "users" not in from_clause
        assert len(query_no_filter.conditions) == 0

    def test_user_filter_with_user_column_selected_compiles(
        self,
        query_user_column_selected: StreamingExportQuery,
    ) -> None:
        """Filtering by user.email while also selecting a user column must compile.

        Selecting a user column LEFT JOINs users into the outer query. The EXISTS subquery
        must keep its own users in FROM (via correlate_except); otherwise users auto-correlates
        out and the subquery is left with no FROM clause ("returned no FROM clauses").
        """
        # users is LEFT JOINed into the outer query because user_email is selected.
        from_clause = str(
            query_user_column_selected.select_from.compile(compile_kwargs={"literal_binds": True})
        )
        assert from_clause.count("LEFT OUTER JOIN users") == 1

        # The full statement (outer join + correlated EXISTS) must compile without raising.
        stmt = (
            sa.select(sa.literal(1))
            .select_from(query_user_column_selected.select_from)
            .where(query_user_column_selected.conditions[0]())
        )
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS (SELECT" in compiled
        assert "users.email" in compiled


_ACTED_AS = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ACTED_AS_OTHER = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

# postgresql.dialect (PGDialect) has an untyped __init__; go through Any to avoid [no-untyped-call].
_pg_dialect_cls: Any = postgresql.dialect
_PG_DIALECT = _pg_dialect_cls()


class TestBuildAuditLogQueryActedAsFilter:
    """Tests for build_audit_log_query acted_as (UUID) filtering (BA-6840).

    The audit-log CSV export must support filtering by the effective actor UUID. The
    ``audit_logs.acted_as`` column is a native ``UUID``; conditions are compiled with the
    PostgreSQL dialect (the production target) so the ``GUID`` type renders values as
    hyphenated UUID literals. These conditions are only exercised through the adapter,
    not the DTO-construction test.
    """

    @pytest.fixture
    def adapter(self) -> ExportAdapter:
        return ExportAdapter()

    @pytest.fixture
    def build_query(
        self,
        adapter: ExportAdapter,
    ) -> Callable[[AuditLogExportFilter], StreamingExportQuery]:
        """Build an audit-log export query, holding the non-varying params constant."""

        def _build(filter: AuditLogExportFilter) -> StreamingExportQuery:
            return adapter.build_audit_log_query(
                report=AUDIT_LOG_REPORT,
                fields=None,
                filter=filter,
                order=None,
                max_rows=1000,
                statement_timeout_sec=60,
            )

        return _build

    @pytest.fixture
    def query_equals(
        self,
        build_query: Callable[[AuditLogExportFilter], StreamingExportQuery],
    ) -> StreamingExportQuery:
        """Filter acted_as by equality."""
        return build_query(AuditLogExportFilter(acted_as=UUIDFilter(equals=_ACTED_AS)))

    @pytest.fixture
    def query_in(
        self,
        build_query: Callable[[AuditLogExportFilter], StreamingExportQuery],
    ) -> StreamingExportQuery:
        """Filter acted_as by set membership."""
        return build_query(
            AuditLogExportFilter(acted_as=UUIDFilter(in_=[_ACTED_AS, _ACTED_AS_OTHER]))
        )

    @pytest.fixture
    def query_not_equals(
        self,
        build_query: Callable[[AuditLogExportFilter], StreamingExportQuery],
    ) -> StreamingExportQuery:
        """Filter acted_as by inequality."""
        return build_query(AuditLogExportFilter(acted_as=UUIDFilter(not_equals=_ACTED_AS)))

    @pytest.fixture
    def query_not_in(
        self,
        build_query: Callable[[AuditLogExportFilter], StreamingExportQuery],
    ) -> StreamingExportQuery:
        """Filter acted_as by negated set membership."""
        return build_query(
            AuditLogExportFilter(acted_as=UUIDFilter(not_in=[_ACTED_AS, _ACTED_AS_OTHER]))
        )

    @pytest.fixture
    def query_no_acted_as(
        self,
        build_query: Callable[[AuditLogExportFilter], StreamingExportQuery],
    ) -> StreamingExportQuery:
        """No acted_as filter set."""
        return build_query(AuditLogExportFilter())

    def test_equals_compiles_to_uuid_equality(
        self,
        query_equals: StreamingExportQuery,
    ) -> None:
        assert len(query_equals.conditions) == 1
        condition = str(
            query_equals.conditions[0]().compile(
                dialect=_PG_DIALECT, compile_kwargs={"literal_binds": True}
            )
        )
        assert f"audit_logs.acted_as = '{_ACTED_AS}'" in condition

    def test_in_compiles_to_uuid_membership(
        self,
        query_in: StreamingExportQuery,
    ) -> None:
        assert len(query_in.conditions) == 1
        condition = str(
            query_in.conditions[0]().compile(
                dialect=_PG_DIALECT, compile_kwargs={"literal_binds": True}
            )
        )
        assert "audit_logs.acted_as IN (" in condition
        assert f"'{_ACTED_AS}'" in condition
        assert f"'{_ACTED_AS_OTHER}'" in condition

    def test_not_equals_compiles_to_negated_equality(
        self,
        query_not_equals: StreamingExportQuery,
    ) -> None:
        assert len(query_not_equals.conditions) == 1
        condition = str(
            query_not_equals.conditions[0]().compile(
                dialect=_PG_DIALECT, compile_kwargs={"literal_binds": True}
            )
        )
        assert f"audit_logs.acted_as != '{_ACTED_AS}'" in condition

    def test_not_in_compiles_to_negated_membership(
        self,
        query_not_in: StreamingExportQuery,
    ) -> None:
        assert len(query_not_in.conditions) == 1
        condition = str(
            query_not_in.conditions[0]().compile(
                dialect=_PG_DIALECT, compile_kwargs={"literal_binds": True}
            )
        )
        assert "audit_logs.acted_as NOT IN (" in condition
        assert f"'{_ACTED_AS}'" in condition
        assert f"'{_ACTED_AS_OTHER}'" in condition

    def test_no_condition_when_acted_as_filter_absent(
        self,
        query_no_acted_as: StreamingExportQuery,
    ) -> None:
        assert query_no_acted_as.conditions == []
