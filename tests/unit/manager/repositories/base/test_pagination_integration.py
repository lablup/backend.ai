"""Integration tests for pagination with real database."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

from ai.backend.manager.repositories.base import (
    BatchQuerier,
    CursorBackwardPagination,
    CursorForwardPagination,
    OffsetPagination,
    QueryCondition,
    execute_batch_querier,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncConnection

    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


@pytest.fixture
async def pagination_test_db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[tuple[AsyncConnection, sa.Table], None]:
    """Create test table with 100 items for pagination testing."""
    metadata = sa.MetaData()
    test_items = sa.Table(
        "test_pagination_items",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    async with database_connection.begin() as conn:
        await conn.run_sync(lambda c: metadata.create_all(c, [test_items]))

        # Insert 100 items with sequential IDs (1-100)
        await conn.execute(
            test_items.insert(),
            [
                {
                    "id": i,
                    "name": f"item-{i:03d}",
                    "created_at": datetime.now(timezone.utc),
                }
                for i in range(1, 101)
            ],
        )

        try:
            yield conn, test_items
        finally:
            await conn.run_sync(lambda c: metadata.drop_all(c, [test_items]))


def _make_base_query(table: sa.Table) -> sa.sql.Select:
    """Create base query without window function (added by execute_batch_querier)."""
    return sa.select(
        table.c.id,
        table.c.name,
    ).select_from(table)


def _make_cursor_condition_forward(table: sa.Table, cursor_id: int) -> QueryCondition:
    """Create forward cursor condition (id > cursor_id)."""

    def condition() -> sa.sql.expression.ColumnElement[bool]:
        return table.c.id > cursor_id

    return condition


def _make_cursor_condition_backward(table: sa.Table, cursor_id: int) -> QueryCondition:
    """Create backward cursor condition (id < cursor_id)."""

    def condition() -> sa.sql.expression.ColumnElement[bool]:
        return table.c.id < cursor_id

    return condition


class TestOffsetPagination:
    """Tests for offset-based pagination."""

    @pytest.mark.parametrize(
        "limit, offset, expected_ids, has_prev, has_next",
        [
            pytest.param(10, 0, list(range(1, 11)), False, True, id="first_page"),
            pytest.param(10, 50, list(range(51, 61)), True, True, id="middle_page"),
            pytest.param(10, 90, list(range(91, 101)), True, False, id="last_page"),
            pytest.param(10, 100, [], True, False, id="beyond_data"),
            pytest.param(100, 0, list(range(1, 101)), False, False, id="single_page"),
            pytest.param(200, 0, list(range(1, 101)), False, False, id="large_limit"),
        ],
    )
    async def test_offset_pagination(
        self,
        pagination_test_db: tuple[AsyncConnection, sa.Table],
        limit: int,
        offset: int,
        expected_ids: list[int],
        has_prev: bool,
        has_next: bool,
    ) -> None:
        """Test offset-based pagination with various scenarios."""
        conn, test_items = pagination_test_db

        query = _make_base_query(test_items).order_by(test_items.c.id.asc())
        querier = BatchQuerier(pagination=OffsetPagination(limit=limit, offset=offset))

        # Use connection as session-like object
        result = await execute_batch_querier(conn, query, querier)  # type: ignore[arg-type]

        actual_ids = [row.id for row in result.rows]
        assert actual_ids == expected_ids
        assert result.total_count == 100
        assert result.has_previous_page == has_prev
        assert result.has_next_page == has_next


class TestCursorForwardPagination:
    """Tests for cursor-based forward pagination (first/after).

    Note: total_count reflects the count with filter conditions only,
    NOT including cursor condition. This represents the full dataset size.
    """

    @pytest.mark.parametrize(
        "first, cursor_id, expected_ids, has_prev, has_next",
        [
            # No cursor: all 100 items, first page
            pytest.param(10, None, list(range(1, 11)), False, True, id="first_page_no_cursor"),
            # After id=10: returns items 11-20, second page
            pytest.param(10, 10, list(range(11, 21)), True, True, id="second_page"),
            # After id=90: returns items 91-100, last page
            pytest.param(10, 90, list(range(91, 101)), True, False, id="last_page"),
            # After id=95: returns items 96-100, partial last
            pytest.param(10, 95, list(range(96, 101)), True, False, id="partial_last"),
            # After id=100: no items after, empty
            pytest.param(10, 100, [], True, False, id="empty_after_end"),
        ],
    )
    async def test_cursor_forward_pagination(
        self,
        pagination_test_db: tuple[AsyncConnection, sa.Table],
        first: int,
        cursor_id: int | None,
        expected_ids: list[int],
        has_prev: bool,
        has_next: bool,
    ) -> None:
        """Test cursor-based forward pagination with various scenarios."""
        conn, test_items = pagination_test_db

        query = _make_base_query(test_items)
        cursor_condition = (
            _make_cursor_condition_forward(test_items, cursor_id) if cursor_id is not None else None
        )
        pagination = CursorForwardPagination(
            first=first,
            cursor_order=test_items.c.id.asc(),
            cursor_condition=cursor_condition,
        )
        querier = BatchQuerier(pagination=pagination)

        result = await execute_batch_querier(conn, query, querier)  # type: ignore[arg-type]

        actual_ids = [row.id for row in result.rows]
        assert actual_ids == expected_ids
        # total_count should always be 100 (full dataset, no filter applied)
        assert result.total_count == 100
        assert result.has_previous_page == has_prev
        assert result.has_next_page == has_next


class TestCursorBackwardPagination:
    """Tests for cursor-based backward pagination (last/before)."""

    @pytest.mark.parametrize(
        "last, cursor_id, expected_ids, has_prev, has_next",
        [
            pytest.param(10, None, list(range(100, 90, -1)), True, False, id="last_page_no_cursor"),
            pytest.param(10, 91, list(range(90, 80, -1)), True, True, id="previous_page"),
            pytest.param(10, 11, list(range(10, 0, -1)), False, True, id="first_page"),
            pytest.param(10, 6, list(range(5, 0, -1)), False, True, id="partial_first"),
        ],
    )
    async def test_cursor_backward_pagination(
        self,
        pagination_test_db: tuple[AsyncConnection, sa.Table],
        last: int,
        cursor_id: int | None,
        expected_ids: list[int],
        has_prev: bool,
        has_next: bool,
    ) -> None:
        """Test cursor-based backward pagination with various scenarios."""
        conn, test_items = pagination_test_db

        query = _make_base_query(test_items)
        cursor_condition = (
            _make_cursor_condition_backward(test_items, cursor_id)
            if cursor_id is not None
            else None
        )
        pagination = CursorBackwardPagination(
            last=last,
            cursor_order=test_items.c.id.desc(),
            cursor_condition=cursor_condition,
        )
        querier = BatchQuerier(pagination=pagination)

        result = await execute_batch_querier(conn, query, querier)  # type: ignore[arg-type]

        actual_ids = [row.id for row in result.rows]
        assert actual_ids == expected_ids
        assert result.total_count == 100
        assert result.has_previous_page == has_prev
        assert result.has_next_page == has_next


class TestPaginationWithFilter:
    """Tests for pagination combined with filter conditions."""

    async def test_offset_pagination_with_filter(
        self,
        pagination_test_db: tuple[AsyncConnection, sa.Table],
    ) -> None:
        """Test offset pagination with WHERE condition."""
        conn, test_items = pagination_test_db

        # Filter: id > 50 (items 51-100, total 50 items)
        def filter_condition() -> sa.sql.expression.ColumnElement[bool]:
            return test_items.c.id > 50

        query = _make_base_query(test_items).order_by(test_items.c.id.asc())
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[filter_condition],
        )

        result = await execute_batch_querier(conn, query, querier)  # type: ignore[arg-type]

        actual_ids = [row.id for row in result.rows]
        assert actual_ids == list(range(51, 61))
        assert result.total_count == 50  # Only 50 items match filter
        assert result.has_previous_page is False
        assert result.has_next_page is True

    async def test_cursor_forward_with_filter(
        self,
        pagination_test_db: tuple[AsyncConnection, sa.Table],
    ) -> None:
        """Test cursor forward pagination with WHERE condition.

        Note: For cursor pagination, total_count reflects filter conditions applied,
        but NOT cursor condition.
        """
        conn, test_items = pagination_test_db

        # Filter: id > 50 (items 51-100)
        def filter_condition() -> sa.sql.expression.ColumnElement[bool]:
            return test_items.c.id > 50

        query = _make_base_query(test_items)
        pagination = CursorForwardPagination(
            first=10,
            cursor_order=test_items.c.id.asc(),
            cursor_condition=None,  # Start from beginning of filtered set
        )
        querier = BatchQuerier(
            pagination=pagination,
            conditions=[filter_condition],
        )

        result = await execute_batch_querier(conn, query, querier)  # type: ignore[arg-type]

        actual_ids = [row.id for row in result.rows]
        assert actual_ids == list(range(51, 61))
        # total_count reflects filter conditions (50 items match id > 50)
        assert result.total_count == 50
        assert result.has_previous_page is False
        assert result.has_next_page is True


class TestEdgeCases:
    """Tests for edge cases."""

    async def test_empty_table(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> None:
        """Test pagination on empty table."""
        metadata = sa.MetaData()
        empty_table = sa.Table(
            "test_pagination_empty",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(50)),
        )

        async with database_connection.begin() as conn:
            await conn.run_sync(lambda c: metadata.create_all(c, [empty_table]))

            try:
                query = sa.select(
                    empty_table.c.id,
                    empty_table.c.name,
                ).select_from(empty_table)

                # Test offset pagination
                querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))
                result = await execute_batch_querier(conn, query, querier)  # type: ignore[arg-type]

                assert result.rows == []
                assert result.total_count == 0
                assert result.has_previous_page is False
                assert result.has_next_page is False

                # Test cursor forward pagination
                querier = BatchQuerier(
                    pagination=CursorForwardPagination(
                        first=10,
                        cursor_order=empty_table.c.id.asc(),
                        cursor_condition=None,
                    )
                )
                result = await execute_batch_querier(conn, query, querier)  # type: ignore[arg-type]

                assert result.rows == []
                assert result.total_count == 0
                assert result.has_previous_page is False
                assert result.has_next_page is False

            finally:
                await conn.run_sync(lambda c: metadata.drop_all(c, [empty_table]))

    async def test_single_item(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> None:
        """Test pagination with single item."""
        metadata = sa.MetaData()
        single_table = sa.Table(
            "test_pagination_single",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(50)),
        )

        async with database_connection.begin() as conn:
            await conn.run_sync(lambda c: metadata.create_all(c, [single_table]))
            await conn.execute(single_table.insert(), [{"id": 1, "name": "only-one"}])

            try:
                query = sa.select(
                    single_table.c.id,
                    single_table.c.name,
                ).select_from(single_table)

                # Test offset pagination
                querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))
                result = await execute_batch_querier(conn, query, querier)  # type: ignore[arg-type]

                assert len(result.rows) == 1
                assert result.rows[0].id == 1
                assert result.total_count == 1
                assert result.has_previous_page is False
                assert result.has_next_page is False

                # Test cursor forward pagination
                querier = BatchQuerier(
                    pagination=CursorForwardPagination(
                        first=10,
                        cursor_order=single_table.c.id.asc(),
                        cursor_condition=None,
                    )
                )
                result = await execute_batch_querier(conn, query, querier)  # type: ignore[arg-type]

                assert len(result.rows) == 1
                assert result.total_count == 1
                assert result.has_previous_page is False
                assert result.has_next_page is False

            finally:
                await conn.run_sync(lambda c: metadata.drop_all(c, [single_table]))

    async def test_exact_boundary(
        self,
        pagination_test_db: tuple[AsyncConnection, sa.Table],
    ) -> None:
        """Test when limit equals total count exactly."""
        conn, test_items = pagination_test_db

        query = _make_base_query(test_items).order_by(test_items.c.id.asc())
        querier = BatchQuerier(pagination=OffsetPagination(limit=100, offset=0))

        result = await execute_batch_querier(conn, query, querier)  # type: ignore[arg-type]

        assert len(result.rows) == 100
        assert result.total_count == 100
        assert result.has_previous_page is False
        assert result.has_next_page is False
