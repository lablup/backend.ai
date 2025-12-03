"""Tests for ScalingGroupConditions and ScalingGroupOrders."""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.manager.repositories.scaling_group.options import (
    ScalingGroupConditions,
    ScalingGroupOrders,
)


class TestScalingGroupConditionsCursor:
    """Tests for cursor-related conditions in ScalingGroupConditions."""

    def test_by_name_greater_than_returns_callable(self) -> None:
        """Test that by_name_greater_than returns a callable QueryCondition."""
        condition = ScalingGroupConditions.by_name_greater_than("test-name")
        assert callable(condition)

    def test_by_name_greater_than_returns_column_element(self) -> None:
        """Test that by_name_greater_than() returns a SQLAlchemy ColumnElement."""
        condition = ScalingGroupConditions.by_name_greater_than("cursor-value")
        result = condition()
        # Result should be a SQLAlchemy expression
        assert isinstance(result, sa.sql.expression.ColumnElement)

    def test_by_name_less_than_returns_callable(self) -> None:
        """Test that by_name_less_than returns a callable QueryCondition."""
        condition = ScalingGroupConditions.by_name_less_than("test-name")
        assert callable(condition)

    def test_by_name_less_than_returns_column_element(self) -> None:
        """Test that by_name_less_than() returns a SQLAlchemy ColumnElement."""
        condition = ScalingGroupConditions.by_name_less_than("cursor-value")
        result = condition()
        # Result should be a SQLAlchemy expression
        assert isinstance(result, sa.sql.expression.ColumnElement)

    def test_by_name_greater_than_uses_closure(self) -> None:
        """Test that by_name_greater_than captures the value in closure."""
        value1 = "value-a"
        value2 = "value-b"

        condition1 = ScalingGroupConditions.by_name_greater_than(value1)
        condition2 = ScalingGroupConditions.by_name_greater_than(value2)

        # Each condition should be independent (different closures)
        result1 = condition1()
        result2 = condition2()

        # Compiled SQL should show different values
        assert str(result1.compile(compile_kwargs={"literal_binds": True})) != str(
            result2.compile(compile_kwargs={"literal_binds": True})
        )

    def test_by_name_less_than_uses_closure(self) -> None:
        """Test that by_name_less_than captures the value in closure."""
        value1 = "value-a"
        value2 = "value-b"

        condition1 = ScalingGroupConditions.by_name_less_than(value1)
        condition2 = ScalingGroupConditions.by_name_less_than(value2)

        # Each condition should be independent (different closures)
        result1 = condition1()
        result2 = condition2()

        # Compiled SQL should show different values
        assert str(result1.compile(compile_kwargs={"literal_binds": True})) != str(
            result2.compile(compile_kwargs={"literal_binds": True})
        )


class TestScalingGroupOrdersCursor:
    """Tests for cursor-related orders in ScalingGroupOrders."""

    def test_name_ascending(self) -> None:
        """Test that name() with ascending=True returns ascending order."""
        order = ScalingGroupOrders.name(ascending=True)
        assert isinstance(order, sa.sql.ClauseElement)
        # Check the modifier shows ASC
        order_str = str(order)
        assert "ASC" in order_str or "asc" in order_str.lower()

    def test_name_descending(self) -> None:
        """Test that name() with ascending=False returns descending order."""
        order = ScalingGroupOrders.name(ascending=False)
        assert isinstance(order, sa.sql.ClauseElement)
        # Check the modifier shows DESC
        order_str = str(order)
        assert "DESC" in order_str or "desc" in order_str.lower()
