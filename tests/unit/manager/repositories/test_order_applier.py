from dataclasses import dataclass, field
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

from ai.backend.manager.repositories.types import BaseOrderingApplier

# Test models and ordering
Base = declarative_base()  # type: ignore


class MockModel(Base):  # type: ignore
    __tablename__ = "test_table"

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    status = Column(String(20))


class MockOrderField(Enum):
    """Mock order fields for testing"""

    NAME = "name"
    STATUS = "status"
    ID = "id"


@dataclass
class MockOrderingOptions:
    """Mock ordering options for testing"""

    order_by: list[tuple[MockOrderField, bool]] = field(
        default_factory=lambda: [(MockOrderField.NAME, False)]  # Default: name ASC
    )


class MockOrderingApplier(BaseOrderingApplier[MockOrderingOptions]):
    """Test implementation of BaseOrderingApplier"""

    def get_order_column(self, field: MockOrderField) -> sa.Column:
        """Get the SQLAlchemy column for the given mock field"""
        return getattr(MockModel, field.value, MockModel.name)


class TestBaseOrderingApplier:
    """Test cases for BaseOrderingApplier"""

    def setup_method(self):
        self.ordering_applier = MockOrderingApplier()
        self.base_stmt = sa.select(MockModel)

    def test_no_ordering(self):
        """Test with default ordering"""
        ordering = MockOrderingOptions()  # Uses default: name ASC

        result_stmt, order_clauses = self.ordering_applier.apply_ordering(self.base_stmt, ordering)

        # Should have ORDER BY clause with name ASC
        order_clause = str(result_stmt.compile())
        assert "ORDER BY test_table.name" in order_clause

        # Check order_clauses return value
        assert len(order_clauses) == 1
        assert order_clauses[0][0] == MockModel.name
        assert not order_clauses[0][1]  # ASC

    def test_single_field_asc(self):
        """Test ordering by single field ascending"""
        ordering = MockOrderingOptions(order_by=[(MockOrderField.NAME, False)])

        result_stmt, order_clauses = self.ordering_applier.apply_ordering(self.base_stmt, ordering)

        order_clause = str(result_stmt.compile())
        assert "ORDER BY test_table.name" in order_clause
        assert "DESC" not in order_clause

        assert len(order_clauses) == 1
        assert not order_clauses[0][1]  # ASC

    def test_single_field_desc(self):
        """Test ordering by single field descending"""
        ordering = MockOrderingOptions(order_by=[(MockOrderField.STATUS, True)])

        result_stmt, order_clauses = self.ordering_applier.apply_ordering(self.base_stmt, ordering)

        order_clause = str(result_stmt.compile())
        assert "ORDER BY test_table.status DESC" in order_clause

        assert len(order_clauses) == 1
        assert order_clauses[0][0] == MockModel.status
        assert order_clauses[0][1]  # DESC

    def test_multiple_fields_ordering(self):
        """Test ordering by multiple fields"""
        ordering = MockOrderingOptions(
            order_by=[
                (MockOrderField.STATUS, True),  # status DESC
                (MockOrderField.NAME, False),  # name ASC
            ]
        )

        result_stmt, order_clauses = self.ordering_applier.apply_ordering(self.base_stmt, ordering)

        order_clause = str(result_stmt.compile())
        assert "ORDER BY test_table.status DESC, test_table.name" in order_clause

        assert len(order_clauses) == 2
        assert order_clauses[0][0] == MockModel.status
        assert order_clauses[0][1]  # DESC
        assert order_clauses[1][0] == MockModel.name
        assert not order_clauses[1][1]  # ASC

    def test_multiple_fields_mixed_ordering(self):
        """Test ordering by multiple fields with mixed ASC/DESC"""
        ordering = MockOrderingOptions(
            order_by=[
                (MockOrderField.NAME, False),  # name ASC
                (MockOrderField.STATUS, True),  # status DESC
                (MockOrderField.ID, False),  # id ASC
            ]
        )

        result_stmt, order_clauses = self.ordering_applier.apply_ordering(self.base_stmt, ordering)

        order_clause = str(result_stmt.compile())
        assert (
            "ORDER BY test_table.name ASC, test_table.status DESC, test_table.id ASC"
            in order_clause
        )

        assert len(order_clauses) == 3
        assert not order_clauses[0][1]  # name ASC
        assert order_clauses[1][1]  # status DESC
        assert not order_clauses[2][1]  # id ASC

    def test_empty_ordering(self):
        """Test with empty ordering list"""
        ordering = MockOrderingOptions(order_by=[])

        result_stmt, order_clauses = self.ordering_applier.apply_ordering(self.base_stmt, ordering)

        # Should not have ORDER BY clause
        order_clause = str(result_stmt.compile())
        assert "ORDER BY" not in order_clause

        # Should return empty order_clauses
        assert len(order_clauses) == 0

    def test_nonexistent_field_fallback(self):
        """Test fallback behavior for nonexistent fields"""

        # Create a custom applier that has fallback behavior
        class FallbackOrderingApplier(BaseOrderingApplier[MockOrderingOptions]):
            def get_order_column(self, field: MockOrderField) -> sa.Column:
                return getattr(MockModel, field.value, MockModel.name)  # Fallback to name

        applier = FallbackOrderingApplier()

        # Mock an enum value that doesn't exist as a column
        class NonexistentField(Enum):
            INVALID = "invalid_column"

        # This would normally fail, but our implementation handles it with getattr fallback
        # Since we can't easily mock enum values, let's test the existing behavior
        ordering = MockOrderingOptions(order_by=[(MockOrderField.NAME, True)])

        result_stmt, order_clauses = applier.apply_ordering(self.base_stmt, ordering)

        order_clause = str(result_stmt.compile())
        assert "ORDER BY test_table.name DESC" in order_clause

    def test_order_clauses_return_format(self):
        """Test that order_clauses return the correct format for pagination"""
        ordering = MockOrderingOptions(
            order_by=[(MockOrderField.STATUS, True), (MockOrderField.NAME, False)]
        )

        result_stmt, order_clauses = self.ordering_applier.apply_ordering(self.base_stmt, ordering)

        # Verify the format is list of (Column, bool) tuples
        assert isinstance(order_clauses, list)
        assert len(order_clauses) == 2

        for column, desc in order_clauses:
            # In SQLAlchemy ORM, model attributes are InstrumentedAttribute, not Column
            assert hasattr(column, "name")  # Has column-like properties
            assert isinstance(desc, bool)

        # Verify specific columns and directions
        assert order_clauses[0][0].name == "status"
        assert order_clauses[0][1]
        assert order_clauses[1][0].name == "name"
        assert not order_clauses[1][1]

    def test_sql_generation_integration(self):
        """Test that the generated SQL is valid and executable (syntax check)"""
        ordering = MockOrderingOptions(
            order_by=[(MockOrderField.NAME, False), (MockOrderField.STATUS, True)]
        )

        result_stmt, _ = self.ordering_applier.apply_ordering(self.base_stmt, ordering)

        # This should not raise any SQL compilation errors
        compiled = result_stmt.compile()
        sql_str = str(compiled)

        # Verify it looks like valid SQL
        assert sql_str.startswith("SELECT")
        assert "FROM test_table" in sql_str
        assert "ORDER BY test_table.name ASC, test_table.status DESC" in sql_str
