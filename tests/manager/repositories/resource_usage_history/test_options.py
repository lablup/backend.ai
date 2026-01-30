"""Tests for resource usage history query conditions and orders."""

from __future__ import annotations

from datetime import date
from operator import eq

import sqlalchemy as sa

from ai.backend.manager.models.resource_usage_history import (
    DomainUsageBucketRow,
    ProjectUsageBucketRow,
    UserUsageBucketRow,
)
from ai.backend.manager.repositories.resource_usage_history.options import (
    DomainUsageBucketConditions,
    ProjectUsageBucketConditions,
    UserUsageBucketConditions,
)


class TestDomainUsageBucketConditions:
    """Tests for DomainUsageBucketConditions."""

    def test_by_period_start_creates_equality_condition(self) -> None:
        """Verify by_period_start creates a period_start == date condition."""
        test_date = date(2024, 1, 15)
        condition = DomainUsageBucketConditions.by_period_start(test_date)

        # Execute the condition factory to get the SQLAlchemy clause
        clause = condition()

        # Verify it's a BinaryExpression (comparison operator)
        assert isinstance(clause, sa.sql.elements.BinaryExpression)
        # Verify the left side is the period_start column
        assert clause.left.key == "period_start"
        # Verify the operator is equality (==)
        assert clause.operator is eq
        # Verify the right side is the test date
        assert clause.right.value == test_date


class TestProjectUsageBucketConditions:
    """Tests for ProjectUsageBucketConditions."""

    def test_by_period_start_creates_equality_condition(self) -> None:
        """Verify by_period_start creates a period_start == date condition."""
        test_date = date(2024, 1, 15)
        condition = ProjectUsageBucketConditions.by_period_start(test_date)

        clause = condition()

        assert isinstance(clause, sa.sql.elements.BinaryExpression)
        assert clause.left.key == "period_start"
        assert clause.operator is eq
        assert clause.right.value == test_date


class TestUserUsageBucketConditions:
    """Tests for UserUsageBucketConditions."""

    def test_by_period_start_creates_equality_condition(self) -> None:
        """Verify by_period_start creates a period_start == date condition."""
        test_date = date(2024, 1, 15)
        condition = UserUsageBucketConditions.by_period_start(test_date)

        clause = condition()

        assert isinstance(clause, sa.sql.elements.BinaryExpression)
        assert clause.left.key == "period_start"
        assert clause.operator is eq
        assert clause.right.value == test_date
