from __future__ import annotations

import base64
import uuid
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import declarative_base

from ai.backend.manager.api.gql_legacy.base import (
    ConnectionArgs,
    FilterExprArg,
    OrderExprArg,
    _build_sql_stmt_from_connection_args,
)
from ai.backend.manager.api.gql_legacy.gql_relay import ConnectionPaginationOrder
from ai.backend.manager.models.minilang.ordering import QueryOrderParser
from ai.backend.manager.models.minilang.queryfilter import QueryFilterParser, WhereClauseType

# ============= Test Case Dataclasses =============


@dataclass
class ExpectedQuery:
    """Expected structure of a query statement."""

    order_by_columns: list[tuple[str, str]]  # [(column, direction), ...]
    where_condition_patterns: list[str]  # Patterns to find in WHERE clause
    has_limit: bool  # Whether LIMIT should be present


@dataclass
class ExpectedStatements:
    """Expected structure for verifying all statements."""

    query: ExpectedQuery
    count_where_patterns: list[str]  # Patterns in count query WHERE (no cursor conditions)
    cursor_conditions_count: int  # Number of cursor conditions generated


# ============= Helper Functions =============


def compile_to_sql(stmt: sa.sql.Select) -> str:
    """Compile SQLAlchemy statement to PostgreSQL SQL string."""
    return str(
        stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


def verify_statements(
    stmt: sa.sql.Select,
    count_stmt: sa.sql.Select,
    conditions: list[WhereClauseType],
    expected: ExpectedStatements,
) -> None:
    """Verify that statements match expected structure."""
    query_sql = compile_to_sql(stmt)
    count_sql = compile_to_sql(count_stmt)

    # Verify ORDER BY in query
    for col, direction in expected.query.order_by_columns:
        # SQLAlchemy may prefix column name with table name
        # Match patterns like "id ASC", "test_table.id ASC", or "test_table_1.id ASC"
        pattern_simple = f"{col} {direction}"
        pattern_prefixed = f".{col} {direction}"
        assert pattern_simple in query_sql or pattern_prefixed in query_sql, (
            f"Expected ORDER BY pattern '{pattern_simple}' (or with table prefix) not found in: {query_sql}"
        )

    # Verify WHERE conditions in query
    for pattern in expected.query.where_condition_patterns:
        assert pattern in query_sql, f"Expected WHERE pattern '{pattern}' not found in: {query_sql}"

    # Verify LIMIT in query
    if expected.query.has_limit:
        assert "LIMIT" in query_sql, f"Expected LIMIT not found in: {query_sql}"

    # Verify count WHERE (should not have cursor conditions, only filter conditions)
    for pattern in expected.count_where_patterns:
        assert pattern in count_sql, (
            f"Expected count WHERE pattern '{pattern}' not found in: {count_sql}"
        )

    # Verify cursor conditions count
    assert len(conditions) == expected.cursor_conditions_count, (
        f"Expected {expected.cursor_conditions_count} cursor conditions, got {len(conditions)}"
    )


# ============= Test Class =============


class TestCursorPaginationBugFixes:
    """Test fixes for cursor pagination bugs BA-3780."""

    # ============= Fixtures =============

    @pytest.fixture
    def cursor_row_id(self) -> uuid.UUID:
        """Test cursor row UUID (dynamically generated)."""
        return uuid.uuid4()

    @pytest.fixture
    def cursor_id(self, cursor_row_id: uuid.UUID) -> str:
        """GraphQL global ID encoded cursor.

        This mimics AsyncNode.to_global_id() format.
        """
        # Format: "TypeName:uuid"
        node_id = f"TestNode:{cursor_row_id}"
        return base64.b64encode(node_id.encode()).decode()

    @pytest.fixture
    def mock_orm_class(self):
        """Create a real declarative ORM class for testing."""
        Base = declarative_base()

        class TestTable(Base):  # type: ignore[misc,valid-type]
            __tablename__ = "test_table"
            id = sa.Column(postgresql.UUID(as_uuid=True), primary_key=True)
            created_at = sa.Column(sa.DateTime(timezone=True))
            name = sa.Column(sa.String(length=255))

        return TestTable

    @pytest.fixture
    def mock_info(self) -> MagicMock:
        """Mock GraphQL ResolveInfo."""
        mock = MagicMock()
        mock.context = MagicMock()
        return mock

    @pytest.fixture(autouse=True)
    def patch_resolve_global_id(self, cursor_row_id: uuid.UUID):
        """Auto-apply patch for AsyncNode.resolve_global_id to all tests."""
        with patch(
            "ai.backend.manager.api.gql_legacy.base.AsyncNode.resolve_global_id",
            return_value=("TestNode", str(cursor_row_id)),
        ):
            yield

    @pytest.fixture
    def order_expr_asc(self) -> OrderExprArg:
        """OrderExprArg for ascending created_at ordering (+created_at)."""
        parser = QueryOrderParser()
        return OrderExprArg(parser=parser, expr="+created_at")

    @pytest.fixture
    def order_expr_desc(self) -> OrderExprArg:
        """OrderExprArg for descending created_at ordering (-created_at)."""
        parser = QueryOrderParser()
        return OrderExprArg(parser=parser, expr="-created_at")

    @pytest.fixture
    def filter_expr(self) -> FilterExprArg:
        """FilterExprArg for name filtering."""
        parser = QueryFilterParser()
        return FilterExprArg(parser=parser, expr='name == "test"')

    # ============= Bug 1 Tests: Pagination without order_expr =============

    @pytest.mark.parametrize(
        "pagination_order,expected",
        [
            pytest.param(
                ConnectionPaginationOrder.FORWARD,
                ExpectedStatements(
                    query=ExpectedQuery(
                        order_by_columns=[("id", "ASC")],
                        where_condition_patterns=["id >"],
                        has_limit=True,
                    ),
                    count_where_patterns=[],
                    cursor_conditions_count=1,
                ),
                id="forward",
            ),
            pytest.param(
                ConnectionPaginationOrder.BACKWARD,
                ExpectedStatements(
                    query=ExpectedQuery(
                        order_by_columns=[("id", "ASC")],
                        where_condition_patterns=["id <"],
                        has_limit=True,
                    ),
                    count_where_patterns=[],
                    cursor_conditions_count=1,
                ),
                id="backward",
            ),
        ],
    )
    async def test_bug1_pagination_without_order_expr(
        self,
        mock_orm_class,
        mock_info,
        cursor_id: str,
        pagination_order: ConnectionPaginationOrder,
        expected: ExpectedStatements,
    ) -> None:
        """Bug 1 fix: cursor pagination works without explicit order_expr.

        When no order_expr is provided, the id-based cursor condition must still be added.
        """
        # Arrange
        connection_args = ConnectionArgs(
            cursor=cursor_id,
            pagination_order=pagination_order,
            requested_page_size=10,
        )

        # Act
        stmt, count_stmt, conditions = _build_sql_stmt_from_connection_args(
            info=mock_info,
            orm_class=mock_orm_class,
            id_column=mock_orm_class.id,
            connection_args=connection_args,
        )

        # Assert
        verify_statements(stmt, count_stmt, conditions, expected)

    # ============= ASC order_expr Tests =============

    @pytest.mark.parametrize(
        "pagination_order,expected",
        [
            pytest.param(
                ConnectionPaginationOrder.FORWARD,
                ExpectedStatements(
                    query=ExpectedQuery(
                        order_by_columns=[("created_at", "ASC"), ("id", "ASC")],
                        where_condition_patterns=["created_at >", "id >"],
                        has_limit=True,
                    ),
                    count_where_patterns=[],
                    cursor_conditions_count=1,
                ),
                id="forward",
            ),
            pytest.param(
                ConnectionPaginationOrder.BACKWARD,
                ExpectedStatements(
                    query=ExpectedQuery(
                        order_by_columns=[("created_at", "DESC"), ("id", "ASC")],
                        where_condition_patterns=["created_at <", "id <"],
                        has_limit=True,
                    ),
                    count_where_patterns=[],
                    cursor_conditions_count=1,
                ),
                id="backward",
            ),
        ],
    )
    async def test_pagination_with_asc_order_expr(
        self,
        mock_orm_class,
        mock_info,
        cursor_id: str,
        order_expr_asc: OrderExprArg,
        pagination_order: ConnectionPaginationOrder,
        expected: ExpectedStatements,
    ) -> None:
        """Cursor pagination with ascending order_expr (+created_at).

        Forward: created_at > cursor OR (created_at = cursor AND id > cursor_id)
        Backward: created_at < cursor OR (created_at = cursor AND id < cursor_id)
        Note: BACKWARD pagination reverses ordering (ASC → DESC in SQL).
        """
        # Arrange
        connection_args = ConnectionArgs(
            cursor=cursor_id,
            pagination_order=pagination_order,
            requested_page_size=10,
        )

        # Act
        stmt, count_stmt, conditions = _build_sql_stmt_from_connection_args(
            info=mock_info,
            orm_class=mock_orm_class,
            id_column=mock_orm_class.id,
            order_expr=order_expr_asc,
            connection_args=connection_args,
        )

        # Assert
        verify_statements(stmt, count_stmt, conditions, expected)

    # ============= DESC order_expr Tests =============

    @pytest.mark.parametrize(
        "pagination_order,expected",
        [
            pytest.param(
                ConnectionPaginationOrder.FORWARD,
                ExpectedStatements(
                    query=ExpectedQuery(
                        order_by_columns=[("created_at", "DESC"), ("id", "ASC")],
                        where_condition_patterns=["created_at <", "id >"],
                        has_limit=True,
                    ),
                    count_where_patterns=[],
                    cursor_conditions_count=1,
                ),
                id="forward",
            ),
            pytest.param(
                ConnectionPaginationOrder.BACKWARD,
                ExpectedStatements(
                    query=ExpectedQuery(
                        order_by_columns=[("created_at", "ASC"), ("id", "ASC")],
                        where_condition_patterns=["created_at >", "id <"],
                        has_limit=True,
                    ),
                    count_where_patterns=[],
                    cursor_conditions_count=1,
                ),
                id="backward",
            ),
        ],
    )
    async def test_pagination_with_desc_order_expr(
        self,
        mock_orm_class,
        mock_info,
        cursor_id: str,
        order_expr_desc: OrderExprArg,
        pagination_order: ConnectionPaginationOrder,
        expected: ExpectedStatements,
    ) -> None:
        """Cursor pagination with descending order_expr (-created_at).

        Forward: created_at < cursor OR (created_at = cursor AND id > cursor_id)
        Backward: created_at > cursor OR (created_at = cursor AND id < cursor_id)
        Note: BACKWARD pagination reverses ordering (DESC → ASC in SQL).
        """
        # Arrange
        connection_args = ConnectionArgs(
            cursor=cursor_id,
            pagination_order=pagination_order,
            requested_page_size=10,
        )

        # Act
        stmt, count_stmt, conditions = _build_sql_stmt_from_connection_args(
            info=mock_info,
            orm_class=mock_orm_class,
            id_column=mock_orm_class.id,
            order_expr=order_expr_desc,
            connection_args=connection_args,
        )

        # Assert
        verify_statements(stmt, count_stmt, conditions, expected)

    # ============= Bug 2 Test: Count query independence =============

    async def test_bug2_count_query_not_affected_by_cursor(
        self,
        mock_orm_class,
        mock_info,
        cursor_id: str,
        filter_expr: FilterExprArg,
    ) -> None:
        """Bug 2 fix: count query is not affected by cursor conditions.

        The count should return the total number of items matching the filter,
        not the number of items after the cursor. This test verifies that:
        1. Filter conditions are applied to both query and count
        2. Cursor conditions are only applied to the query, not the count
        """
        # Arrange
        connection_args_with_cursor = ConnectionArgs(
            cursor=cursor_id,
            pagination_order=ConnectionPaginationOrder.FORWARD,
            requested_page_size=10,
        )
        connection_args_without_cursor = ConnectionArgs(
            cursor=None,
            pagination_order=ConnectionPaginationOrder.FORWARD,
            requested_page_size=10,
        )

        # Act - with cursor
        stmt_with_cursor, count_stmt_with_cursor, conditions_with_cursor = (
            _build_sql_stmt_from_connection_args(
                info=mock_info,
                orm_class=mock_orm_class,
                id_column=mock_orm_class.id,
                filter_expr=filter_expr,
                connection_args=connection_args_with_cursor,
            )
        )

        # Act - without cursor
        _, count_stmt_without_cursor, conditions_without_cursor = (
            _build_sql_stmt_from_connection_args(
                info=mock_info,
                orm_class=mock_orm_class,
                id_column=mock_orm_class.id,
                filter_expr=filter_expr,
                connection_args=connection_args_without_cursor,
            )
        )

        # Assert - count queries should be identical (Bug 2 fix)
        count_sql_with_cursor = compile_to_sql(count_stmt_with_cursor)
        count_sql_without_cursor = compile_to_sql(count_stmt_without_cursor)

        assert count_sql_with_cursor == count_sql_without_cursor

        # Assert - query with cursor should have cursor conditions
        query_sql_with_cursor = compile_to_sql(stmt_with_cursor)
        assert "id >" in query_sql_with_cursor

        # Assert - count query should only have filter conditions, not cursor conditions
        assert "name" in count_sql_with_cursor
        assert "id >" not in count_sql_with_cursor

        # Assert - conditions list should include both filter and cursor
        assert len(conditions_with_cursor) == 2
        assert len(conditions_without_cursor) == 1
