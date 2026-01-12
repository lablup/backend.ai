"""Tests for ScalingGroupConditions and ScalingGroupOrders."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.scaling_group.options import (
    ScalingGroupConditions,
    ScalingGroupOrders,
)
from ai.backend.testutils.db import with_tables

# Define the tables list in FK dependency order for mapper initialization
_WITH_TABLES = [
    DomainRow,
    ScalingGroupRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    UserRoleRow,
    UserRow,
    KeyPairRow,
    GroupRow,
    ImageRow,
    VFolderRow,
    EndpointRow,
    DeploymentPolicyRow,
    DeploymentAutoScalingPolicyRow,
    DeploymentRevisionRow,
    SessionRow,
    AgentRow,
    KernelRow,
    RoutingRow,
    ResourcePresetRow,
]


@pytest.fixture
async def db_with_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    """Database connection with tables created for SQLAlchemy mapper initialization."""
    async with with_tables(database_connection, _WITH_TABLES):
        yield database_connection


class TestScalingGroupConditionsCursor:
    """Tests for cursor-related conditions in ScalingGroupConditions."""

    def test_by_cursor_forward_returns_callable(self) -> None:
        """Test that by_cursor_forward returns a callable QueryCondition."""
        condition = ScalingGroupConditions.by_cursor_forward("test-name")
        assert callable(condition)

    def test_by_cursor_forward_returns_column_element(self) -> None:
        """Test that by_cursor_forward() returns a SQLAlchemy ColumnElement."""
        condition = ScalingGroupConditions.by_cursor_forward("cursor-value")
        result = condition()
        # Result should be a SQLAlchemy expression
        assert isinstance(result, sa.sql.expression.ColumnElement)

    def test_by_cursor_backward_returns_callable(self) -> None:
        """Test that by_cursor_backward returns a callable QueryCondition."""
        condition = ScalingGroupConditions.by_cursor_backward("test-name")
        assert callable(condition)

    def test_by_cursor_backward_returns_column_element(self) -> None:
        """Test that by_cursor_backward() returns a SQLAlchemy ColumnElement."""
        condition = ScalingGroupConditions.by_cursor_backward("cursor-value")
        result = condition()
        # Result should be a SQLAlchemy expression
        assert isinstance(result, sa.sql.expression.ColumnElement)

    def test_by_cursor_forward_uses_closure(self) -> None:
        """Test that by_cursor_forward captures the value in closure."""
        value1 = "value-a"
        value2 = "value-b"

        condition1 = ScalingGroupConditions.by_cursor_forward(value1)
        condition2 = ScalingGroupConditions.by_cursor_forward(value2)

        # Each condition should be independent (different closures)
        result1 = condition1()
        result2 = condition2()

        # Compiled SQL should show different values
        assert str(result1.compile(compile_kwargs={"literal_binds": True})) != str(
            result2.compile(compile_kwargs={"literal_binds": True})
        )

    def test_by_cursor_backward_uses_closure(self) -> None:
        """Test that by_cursor_backward captures the value in closure."""
        value1 = "value-a"
        value2 = "value-b"

        condition1 = ScalingGroupConditions.by_cursor_backward(value1)
        condition2 = ScalingGroupConditions.by_cursor_backward(value2)

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
