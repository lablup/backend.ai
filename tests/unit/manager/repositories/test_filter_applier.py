from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sqlalchemy as sa
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import Select

from ai.backend.manager.repositories.types import BaseFilterApplier

# Test models and filters
Base = declarative_base()


class MockModel(Base):  # type: ignore
    __tablename__ = "test_table"

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    status = Column(String(20))


@dataclass
class MockFilterOptions:
    """Test filter options with logical operations support"""

    name: str | None = None
    status: str | None = None

    # Logical operations
    AND: list["MockFilterOptions"] | None = None
    OR: list["MockFilterOptions"] | None = None
    NOT: list["MockFilterOptions"] | None = None


class MockFilterApplier(BaseFilterApplier[MockFilterOptions]):
    """Test implementation of BaseFilterApplier"""

    def apply_entity_filters(
        self, stmt: Select[Any], filters: MockFilterOptions
    ) -> tuple[list[Any], Select[Any]]:
        """Apply test-specific filters"""
        conditions = []

        if filters.name is not None:
            conditions.append(MockModel.name == filters.name)
        if filters.status is not None:
            conditions.append(MockModel.status == filters.status)

        return conditions, stmt


class TestBaseFilterApplier:
    """Test cases for BaseFilterApplier"""

    def setup_method(self) -> None:
        self.filter_applier = MockFilterApplier()
        self.base_stmt = sa.select(MockModel)

    def test_no_filters(self) -> None:
        """Test with empty filter options"""
        filters = MockFilterOptions()

        result_stmt = self.filter_applier.apply_filters(self.base_stmt, filters)

        # Should return original statement when no filters are applied
        assert str(result_stmt) == str(self.base_stmt)

    def test_simple_filters(self) -> None:
        """Test basic entity filters"""
        filters = MockFilterOptions(name="test", status="active")

        result_stmt = self.filter_applier.apply_filters(self.base_stmt, filters)

        # Should have WHERE clause with both conditions
        where_clause = str(result_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "test_table.name = 'test'" in where_clause
        assert "test_table.status = 'active'" in where_clause
        assert "AND" in where_clause

    def test_single_filter(self) -> None:
        """Test with only one filter"""
        filters = MockFilterOptions(name="test")

        result_stmt = self.filter_applier.apply_filters(self.base_stmt, filters)

        where_clause = str(result_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "test_table.name = 'test'" in where_clause
        # Check that there's only one WHERE condition (no status filter)
        assert "WHERE test_table.name = 'test'" in where_clause

    def test_and_operation(self) -> None:
        """Test AND logical operation"""
        filters = MockFilterOptions(
            AND=[MockFilterOptions(name="test1"), MockFilterOptions(status="active")]
        )

        result_stmt = self.filter_applier.apply_filters(self.base_stmt, filters)

        where_clause = str(result_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "test_table.name = 'test1'" in where_clause
        assert "test_table.status = 'active'" in where_clause
        assert "AND" in where_clause

    def test_or_operation(self) -> None:
        """Test OR logical operation"""
        filters = MockFilterOptions(
            OR=[MockFilterOptions(name="test1"), MockFilterOptions(name="test2")]
        )

        result_stmt = self.filter_applier.apply_filters(self.base_stmt, filters)

        where_clause = str(result_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "test_table.name = 'test1'" in where_clause
        assert "test_table.name = 'test2'" in where_clause
        assert "OR" in where_clause

    def test_not_operation(self) -> None:
        """Test NOT logical operation"""
        filters = MockFilterOptions(NOT=[MockFilterOptions(status="inactive")])

        result_stmt = self.filter_applier.apply_filters(self.base_stmt, filters)

        where_clause = str(result_stmt.compile(compile_kwargs={"literal_binds": True}))
        # SQLAlchemy renders NOT as != for simple conditions
        assert "test_table.status != 'inactive'" in where_clause

    def test_combined_base_and_logical_filters(self) -> None:
        """Test combination of base filters and logical operations"""
        filters = MockFilterOptions(
            name="base_name",
            OR=[MockFilterOptions(status="active"), MockFilterOptions(status="pending")],
        )

        result_stmt = self.filter_applier.apply_filters(self.base_stmt, filters)

        where_clause = str(result_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "test_table.name = 'base_name'" in where_clause
        assert "test_table.status = 'active'" in where_clause
        assert "test_table.status = 'pending'" in where_clause
        assert "OR" in where_clause

    def test_nested_logical_operations(self) -> None:
        """Test nested logical operations"""
        filters = MockFilterOptions(
            AND=[
                MockFilterOptions(name="test"),
                MockFilterOptions(
                    OR=[MockFilterOptions(status="active"), MockFilterOptions(status="pending")]
                ),
            ]
        )

        result_stmt = self.filter_applier.apply_filters(self.base_stmt, filters)

        where_clause = str(result_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "test_table.name = 'test'" in where_clause
        assert "test_table.status = 'active'" in where_clause
        assert "test_table.status = 'pending'" in where_clause
        assert "AND" in where_clause
        assert "OR" in where_clause

    def test_multiple_not_operations(self) -> None:
        """Test multiple NOT operations"""
        filters = MockFilterOptions(
            NOT=[MockFilterOptions(status="inactive"), MockFilterOptions(name="excluded")]
        )

        result_stmt = self.filter_applier.apply_filters(self.base_stmt, filters)

        where_clause = str(result_stmt.compile(compile_kwargs={"literal_binds": True}))
        # Multiple NOT conditions are combined with AND inside a NOT clause
        assert "NOT (" in where_clause
        assert "test_table.status = 'inactive'" in where_clause
        assert "test_table.name = 'excluded'" in where_clause
        assert "AND" in where_clause

    def test_empty_logical_operations(self) -> None:
        """Test empty logical operation lists"""
        filters = MockFilterOptions(name="test", AND=[], OR=[], NOT=[])

        result_stmt = self.filter_applier.apply_filters(self.base_stmt, filters)

        where_clause = str(result_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "test_table.name = 'test'" in where_clause
        # Empty logical operations should not affect the query

    def test_complex_combination(self) -> None:
        """Test complex combination of all logical operations"""
        filters = MockFilterOptions(
            name="base",
            AND=[MockFilterOptions(status="active")],
            OR=[MockFilterOptions(name="alt1"), MockFilterOptions(name="alt2")],
            NOT=[MockFilterOptions(status="deleted")],
        )

        result_stmt = self.filter_applier.apply_filters(self.base_stmt, filters)

        where_clause = str(result_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "test_table.name = 'base'" in where_clause
        assert "test_table.status = 'active'" in where_clause
        assert "test_table.name = 'alt1'" in where_clause
        assert "test_table.name = 'alt2'" in where_clause
        # NOT operation renders as != for simple conditions
        assert "test_table.status != 'deleted'" in where_clause
        assert "AND" in where_clause
        assert "OR" in where_clause
